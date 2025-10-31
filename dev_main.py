
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import base64
import logging
import shutil
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent

# 依存パッケージ（あなたの環境に合わせて）
from agents import set_default_openai_client, Agent, Runner
from agents.mcp import MCPServerStdio

load_dotenv()


def parse_args():
    p = argparse.ArgumentParser(description="FreeCAD MCP + OpenAI ストリーミングREPL")
    p.add_argument("--model", default="gpt-4.1", help="使用するOpenAIモデル（例: gpt-4.1, gpt-4.1-mini, o4-mini）")
    p.add_argument("--doc-name", default="Main", help="作業に使用するFreeCADドキュメント名")
    p.add_argument(
        "--server-dir",
        default=r"C:\Users\USER\Documents\3dprinterrrr\mcp-server\freecad-mcp",
        help="freecad-mcp のディレクトリ",
    )
    p.add_argument("--only-text-feedback", action="store_true", help="MCPをテキスト出力モードで起動")
    p.add_argument("--log-level", default="INFO", help="ログレベル（DEBUG/INFO/WARNING/ERROR）")
    return p.parse_args()


ARGS = parse_args()
logging.basicConfig(level=getattr(logging, ARGS.log_level.upper(), logging.INFO))


SYSTEM_INSTRUCTIONS_TEMPLATE = """
あなたはFreeCAD MCPツールを使うCADオペレータです。
必ずミリメートル(mm)単位で寸法を明示してください。
doc_name={DOC_NAME}を使用すること
各ターンで行うこと:
1) 実行計画(簡潔)
2) 実行するMCPツール呼び出し（作成/編集の対象名・寸法）
3) 生成/変更したオブジェクト名の一覧（今後参照するため）
4) 失敗時は原因と次の打ち手
出力はテキスト中心。画像は返さないでください。
""".strip()


def make_server() -> MCPServerStdio:
    """uv存在確認のうえで MCPServerStdio を生成"""
    if shutil.which("uv") is None:
        raise RuntimeError("uv が見つかりません。'pipx install uv' などで導入してください。")

    uv_args = ["--directory", ARGS.server_dir, "run", "freecad-mcp"]
    if ARGS.only_text_feedback:
        uv_args.append("--only-text-feedback")

    return MCPServerStdio(
        name="FreeCAD via uv",
        params={"command": "uv", "args": uv_args},
        client_session_timeout_seconds=180,
    )


async def ensure_document(server: MCPServerStdio, doc_name: str) -> None:
    """
    FreeCADドキュメント doc_name を必ず準備する。
    - 無ければ create_document
    - アクティブ化 set_active_document
    - ビュー初期化は任意（失敗は握りつぶし）
    """
    try:
        docs = await server.call_tool("get_documents", {})
        names = []
        if isinstance(docs, list):
            for d in docs:
                # 実装差異吸収: Name or name
                names.append(d.get("Name") or d.get("name"))

        if doc_name not in names:
            logging.info("Document '%s' not found. Creating...", doc_name)
            await server.call_tool("create_document", {"name": doc_name})

        await server.call_tool("set_active_document", {"doc_name": doc_name})

        # ビュー初期化（オプション）
        try:
            await server.call_tool("get_view", {"doc_name": doc_name})
            await server.call_tool(
                "set_view",
                {"doc_name": doc_name, "viewAxonometric": True, "fitAll": True},
            )
        except Exception as e:
            logging.debug("View init skipped: %s", e)

    except Exception as e:
        logging.error("ensure_document failed: %s", e)
        raise


def inject_doc_name(user_text: str, doc_name: str) -> str:
    """
    モデルの取りこぼし対策として、各プロンプト先頭に隠し指示を付与。
    - すべてのMCPツール引数に doc_name を必ず含める
    - 寸法はmm
    """
    prefix = f"(必ず全MCPツール引数に doc_name='{doc_name}' を含め、寸法はmmで明示してください)\n"
    return prefix + user_text


async def stream_once(agent: Agent, user_text: str, save_image_path: Optional[str] = None) -> None:
    """
    1ターン分の対話を実行し、テキストΔを逐次表示。
    画像イベント（ある場合）をBase64連結して任意保存。
    """
    result = Runner.run_streamed(agent, user_text)
    image_bufs: list[str] = []

    async for event in result.stream_events():
        et = getattr(event, "type", "")
        data = getattr(event, "data", None)

        # --- テキストΔ（イベント名はSDKにより揺れるため幅広く対応） ---
        if et in ("raw_response_event", "response.output_text.delta", "response.text.delta"):
            delta = None
            if isinstance(data, ResponseTextDeltaEvent):
                delta = data.delta
            else:
                delta = getattr(data, "delta", None) or getattr(data, "text", None)
            if isinstance(delta, str):
                print(delta, end="", flush=True)

        # --- 画像Δ（Base64） ---
        elif et in ("response.output_image.delta", "response.image.delta", "raw_response_event_image"):
            delta = getattr(data, "delta", None) or getattr(data, "b64_json", "")
            if isinstance(delta, str):
                image_bufs.append(delta)

        # --- 完了時 ---
        elif et in ("response.completed", "stream.end"):
            if save_image_path and image_bufs:
                b64 = "".join(image_bufs)
                # Base64 padding 補正
                pad = len(b64) % 4
                if pad:
                    b64 += "=" * (4 - pad)
                try:
                    with open(save_image_path, "wb") as f:
                        f.write(base64.b64decode(b64))
                    print(f"\n[画像を {save_image_path} として保存しました]")
                except Exception as e:
                    logging.warning("画像保存に失敗: %s", e)

    print()  # 行末


async def main():
    # OpenAIクライアントの準備（環境変数 OPENAI_API_KEY を使用）
    openai_client = AsyncOpenAI()
    set_default_openai_client(openai_client, use_for_tracing=True)

    server: Optional[MCPServerStdio] = None

    try:
        # MCPサーバ接続
        server = make_server()
        print("[起動] MCPサーバへ接続中…")
        await server.connect()

        tools = await server.list_tools()
        logging.info("[MCPツール] %s", [t.name for t in tools])
        logging.info("[モデル] %s", ARGS.model)
        logging.info("[ドキュメント] %s", ARGS.doc_name)

        # ドキュメント準備（存在保証）
        await ensure_document(server, ARGS.doc_name)

        # システムプロンプト
        system_instructions = SYSTEM_INSTRUCTIONS_TEMPLATE.format(DOC_NAME=ARGS.doc_name)

        # エージェント生成
        agent = Agent(
            name="Assistant",
            instructions=system_instructions,
            mcp_servers=[server],
            model=ARGS.model,
        )

        # ウォームアップ（任意のクエリ）
        print("==== FreeCAD 対話モード ====")
        print("例: 『半径30mmの球を作成』『Sphere_001を半径40mmに変更』『前回の球と50mm角立方体を和集合』など")
        print("終了するには: /exit")

        # 最初の一言（人工衛星：typo修正済み）
        await stream_once(agent, inject_doc_name("FreeCADで人工衛星を作ってください", ARGS.doc_name))

        # REPL
        while True:
            try:
                user_text = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[終了要求]")
                break

            if not user_text:
                continue
            if user_text.lower() in ("/exit", "exit", "quit", "/q"):
                break

            await stream_once(agent, inject_doc_name(user_text, ARGS.doc_name))

    except asyncio.CancelledError:
        logging.warning("cancelled")
        raise
    except Exception as e:
        logging.exception("fatal error: %s", e)
    finally:
        # クリーンアップは確実に
        if server:
            try:
                await server.cleanup()
            except Exception:
                pass
        try:
            await openai_client.aclose()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
