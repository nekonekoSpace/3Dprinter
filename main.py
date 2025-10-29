import asyncio
import base64
import sys
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from agents import set_default_openai_client, Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
load_dotenv()

# ★APIキーは環境変数 OPENAI_API_KEY を推奨（直書きしない）
#   openai_client = AsyncOpenAI() なら環境変数から自動読込


DOC_NAME = "Main"

SYSTEM_INSTRUCTIONS = f"""
あなたはFreeCAD MCPツールを使うCADオペレータです。
必ずミリメートル(mm)単位で寸法を明示してください。
doc_name={DOC_NAME}を使用すること
各ターンで行うこと:
1) 実行計画(簡潔)
2) 実行するMCPツール呼び出し（作成/編集の対象名・寸法）
3) 生成/変更したオブジェクト名の一覧（今後参照するため）
4) 失敗時は原因と次の打ち手
出力はテキスト中心。画像は返さないでください。
"""

# SYSTEM_INSTRUCTIONS2 = f"""
# あなたはFreeCAD MCPツールを使うCADオペレータです。
# 必ずミリメートル(mm)単位で寸法を明示してください。
# doc_name={DOC_NAME}を使用すること。 create_documentを行って、ドキュメント作成は行わなくてよいです
# 各ターンで行うこと:
# 1) 実行計画(簡潔)
# 2) 実行するMCPツール呼び出し（作成/編集の対象名・寸法）
# 3) 生成/変更したオブジェクト名の一覧（今後参照するため）
# 4) 失敗時は原因と次の打ち手
# 出力はテキスト中心。画像は返さないでください。
# """

# SYSTEM_INSTRUCTIONS = f"""
# あなたはFreeCAD MCPツールを使うCADオペレータです。
# 作業するFreeCADドキュメント名は常に "{DOC_NAME}" とします。
# 必ず以下の順序に従ってください:
# 2) 無ければ `create_document` で "{DOC_NAME}" を作成。既にあれば作成しない。
# 3) 以降の全ツール呼び出しで doc_name="{DOC_NAME}" を必ず指定。
# 出力は簡潔な計画・実行したツールと引数・作成/変更したオブジェクト名一覧。
# 画像は返さないでください（必要時だけ明示的に返す）。
# 寸法はmmで明示。
# """

def make_server() -> MCPServerStdio:
    return MCPServerStdio(
        name="FreeCAD via uv",
        params={
            "command": "uv",
            "args": [
                "--directory",
                # ★あなたのfreecad-mcpの場所
                r"C:\Users\neko\Downloads\3dprinter\mcp-server\freecad-mcp",
                "run",
                "freecad-mcp",
                 "--only-text-feedback",
            ],
        },
        client_session_timeout_seconds=180,  # 少し長め
    )

async def stream_once(agent: Agent, user_text: str, save_image_path: str | None = None):
    """
    1ターン分: ユーザーの発話を投げ、テキストは逐次print。
    画像イベントが来たら、save_image_pathが指定されていれば保存（なければ捨てる）。
    """
    result = Runner.run_streamed(agent, user_text)
    image_bufs: list[str] = []

    async for event in result.stream_events():
        # --- テキストΔ ---
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

        # --- 画像Δ（SDKのイベント名は環境により差異があるため複数候補で分岐）---
        elif event.type in ("response.output_image.delta", "response.image.delta", "raw_response_event_image"):
            # data.delta or data.b64_json のどちらか
            delta = getattr(event.data, "delta", None) or getattr(event.data, "b64_json", "")
            if isinstance(delta, str):
                image_bufs.append(delta)

        # --- 完了時 ---
        elif event.type in ("response.completed", "stream.end"):
            if save_image_path and image_bufs:
                b64 = "".join(image_bufs)
                with open(save_image_path, "wb") as f:
                    f.write(base64.b64decode(b64))
                print(f"\n[画像を {save_image_path} として保存しました]")
    print()  # ターンの最後で改行

async def main():
    # ★環境変数OPENAI_API_KEYを事前にセット推奨
    openai_client = AsyncOpenAI()  # api_key省略→環境変数から
    # set_default_openai_client(openai_client, use_for_tracing=False)
    set_default_openai_client(openai_client, use_for_tracing=True)

    server = make_server()
    print("[起動] MCPサーバへ接続中…")
    await server.connect()

    tools = await server.list_tools()
    print("[MCPツール] ", [t.name for t in tools])

    agent = Agent(
        name="Assistant",
        instructions=SYSTEM_INSTRUCTIONS,
        mcp_servers=[server],
        # model="gpt-4o",  # 手元の契約に合わせて（gpt-4.1-mini / o4-mini 等でもOK）
        model="gpt-4.1",  # 手元の契約に合わせて（gpt-4.1-mini / o4-mini 等でもOK）
    )

    print("==== FreeCAD 対話モード ====")
    print("例: 『半径30mmの球を作成』『Sphere_001を半径40mmに変更』『前回の球と50mm角立方体を和集合』など")
    print("終了するには: /exit")

    # 最初の一言（あなたのサンプルと同じ）
    # await stream_once(agent, f"`create_document` で {DOC_NAME}を作成したうえで人工衛星を作ってください。", save_image_path=None)

    await stream_once(agent, "FreeCADで人口衛星を作ってください", save_image_path=None)

    # REPL
    while True:
        try:
            user_text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_text:
            continue
        if user_text.lower() in ("/exit", "exit", "quit", "/q"):
            break

        # 必要に応じて画像を保存したいときだけパスを渡す
        # ふだんは None で捨てる（＝コンソールにBase64が出てこない）
        await stream_once(agent, "create_documentを行って、ドキュメント作成は行わなくてよいです."+user_text, save_image_path=None)

    await server.cleanup()
    await openai_client.close()

if __name__ == "__main__":
    asyncio.run(main())
