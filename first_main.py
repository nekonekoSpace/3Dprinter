from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from agents import set_default_openai_client, Agent, Runner
import asyncio
from agents.mcp import MCPServerStdio
import base64


async def main():
    openai_client = AsyncOpenAI(
        api_key=api_key,
    )

    # Set the default OpenAI client for the Agents SDK
    # set trace off because of recomendation from OpenAI
    set_default_openai_client(openai_client, use_for_tracing=False)
    server = MCPServerStdio(
        name="Weather Server, via uv",
        # params={
        #     "command": "uv",
        #     "args": ["run", r"C:\Users\neko\Downloads\3dprinter\mcp-server\wet.py"],
        # },
        params={
            "command": "uv",
            "args": [
                "--directory",
                r"C:\\Users\\neko\Downloads\\3dprinter\\mcp-server\\freecad-mcp",
                "run", 
                "freecad-mcp",
                ],
        },
        client_session_timeout_seconds =120
    )
    print("neko")
    try:
        await server.connect()


        tools = await server.list_tools()
        print(tools)
        agent = Agent(
            name="Assistant",
            instructions="freecadを使って質問に回答してください。",
            mcp_servers=[server],
            model="gpt-4o"
        )

        result = Runner.run_streamed(agent, "FreeCADで3cmの球体を作ってください")
        # result = Runner.run_streamed(agent, "freecadを使って1cm四方の四角形をさらに上にくっつけてください")

        # for i, out in enumerate(result.outputs):
        #     if getattr(out, "type", None) in ("image", "output_image"):
        #         b64 = getattr(out.image, "base64", None) or getattr(out, "b64_json", None)
        #         if b64:
        #             with open(f"freecad_output_{i}.png", "wb") as f:
        #                 f.write(base64.b64decode(b64))
        #     elif getattr(out, "type", None) in ("text", "output_text"):
        #         print(out.text, end="")
        


        image_bufs = []
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)

            elif event.type in ("response.output_image.delta", "response.image.delta", "raw_response_event_image"):
                # 一部SDKでは event.data.delta が base64文字列チャンク
                # もしくは event.data.b64_json という名前のことも
                delta = getattr(event.data, "delta", None) or getattr(event.data, "b64_json", "")
                if isinstance(delta, str):
                    image_bufs.append(delta)

            elif event.type in ("response.completed", "stream.end"):
                if image_bufs:
                    b64 = "".join(image_bufs)
                    with open("freecad_output.png", "wb") as f:
                        f.write(base64.b64decode(b64))
                    print("\n[画像を freecad_output.png として保存しました]")


    finally:
        await server.cleanup()
        await openai_client.close()

if __name__ == "__main__":
    asyncio.run(main())
