#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import json
import logging
import shutil
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents.mcp import MCPServerStdio

load_dotenv()


def parse_args():
    p = argparse.ArgumentParser(description="FreeCAD MCP + OpenAI 直接呼び出しREPL")
    p.add_argument("--model", default="gpt-4o", help="使用するOpenAIモデル（例: gpt-4o, gpt-4o-mini）")
    p.add_argument("--doc-name", default="Main", help="作業に使用するFreeCADドキュメント名")
    p.add_argument(
        "--server-dir",
        default=r"C:\Users\USER\Documents\3dprinterrrr\mcp-server\freecad-mcp",
        help="freecad-mcp のディレクトリ",
    )
    p.add_argument("--only-text-feedback", action="store_true", help="MCPをテキスト出力モードで起動")
    p.add_argument("--log-level", default="INFO", help="ログレベル（DEBUG/INFO/WARNING/ERROR）")
    p.add_argument("--show-tool-calls", action="store_true", help="ツール呼び出しと結果を詳細表示")
    p.add_argument("--max-turns", type=int, default=30, help="1クエリあたりの最大ターン数")
    return p.parse_args()


ARGS = parse_args()
logging.basicConfig(level=getattr(logging, ARGS.log_level.upper(), logging.INFO))


SYSTEM_INSTRUCTIONS_TEMPLATE = """
あなたはFreeCAD MCPツールを使うCADオペレータです。
必ずミリメートル(mm)単位で寸法を明示してください。
doc_name={DOC_NAME}を使用すること

【重要】ツール結果の扱い:
- すべてのツール呼び出しは成功します
- get_object, get_objects などの結果を正確に読み取ってください
- 座標、寸法、プロパティ情報を具体的に報告してください

各ターンで行うこと:
1) 実行計画(簡潔)
2) 実行するMCPツール呼び出し（作成/編集の対象名・寸法）
3) ツール結果の詳細な報告（座標、寸法など具体的な数値）
4) 生成/変更したオブジェクト名の一覧

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
    """FreeCADドキュメント doc_name を必ず準備する"""
    try:
        docs = await server.call_tool("get_documents", {})
        names = []
        if isinstance(docs, list):
            for d in docs:
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


def mcp_tool_to_openai_function(tool) -> Dict[str, Any]:
    """MCPツールをOpenAIのfunction形式に変換"""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or f"MCP tool: {tool.name}",
            "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }


def format_tool_result(result) -> str:
    """ツール結果を読みやすくフォーマット"""
    # CallToolResult オブジェクトの処理
    if hasattr(result, 'content'):
        text_parts = []
        for item in result.content:
            if hasattr(item, 'type'):
                if item.type == 'text':
                    text_parts.append(item.text)
                elif item.type == 'image':
                    text_parts.append('[画像データ]')
        return '\n'.join(text_parts) if text_parts else str(result)
    elif isinstance(result, dict):
        return json.dumps(result, ensure_ascii=False, indent=2)
    elif isinstance(result, list):
        return json.dumps(result, ensure_ascii=False, indent=2)
    else:
        return str(result)


def inject_doc_name(user_text: str, doc_name: str) -> str:
    """モデルの取りこぼし対策として、各プロンプト先頭に隠し指示を付与"""
    prefix = f"(必ず全MCPツール引数に doc_name='{doc_name}' を含め、寸法はmmで明示してください)\n"
    return prefix + user_text


async def chat_with_tools(
    client: AsyncOpenAI,
    server: MCPServerStdio,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    model: str
) -> tuple[str, List[Dict[str, Any]]]:
    """
    OpenAI APIを使ってツール呼び出しを含む会話を実行
    
    Returns:
        (最終的なアシスタントの応答, 更新されたメッセージ履歴)
    """
    current_messages = messages.copy()
    
    for turn in range(ARGS.max_turns):
        logging.debug(f"Turn {turn + 1}/{ARGS.max_turns}")
        
        # OpenAI APIを呼び出し
        response = await client.chat.completions.create(
            model=model,
            messages=current_messages,
            tools=tools,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        # アシスタントのメッセージを履歴に追加
        current_messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
        })
        
        # アシスタントの応答を表示
        if assistant_message.content:
            print(assistant_message.content, flush=True)
        
        # ツール呼び出しがなければ終了
        if not assistant_message.tool_calls:
            break
        
        # ツール呼び出しを処理
        print("\n" + "="*60)
        print("🔧 ツール呼び出し")
        print("="*60)
        
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            if ARGS.show_tool_calls:
                print(f"\n📌 {tool_name}")
                print(f"   引数: {json.dumps(tool_args, ensure_ascii=False)}")
            
            # MCPサーバーでツールを実行
            try:
                tool_result = await server.call_tool(tool_name, tool_args)
                
                # CallToolResult を文字列に変換
                if hasattr(tool_result, 'content'):
                    # content リストからテキストのみ抽出
                    text_parts = []
                    for item in tool_result.content:
                        if hasattr(item, 'type') and item.type == 'text':
                            text_parts.append(item.text)
                    tool_result_str = '\n'.join(text_parts) if text_parts else str(tool_result)
                else:
                    tool_result_str = json.dumps(tool_result, ensure_ascii=False) if isinstance(tool_result, (dict, list)) else str(tool_result)
                
                # 結果を表示
                print(f"\n📊 結果:")
                formatted_result = format_tool_result(tool_result)
                if len(formatted_result) > 1000:
                    print(formatted_result[:1000])
                    print("... (省略)")
                else:
                    print(formatted_result)
                
                # ツール結果をメッセージ履歴に追加（文字列として）
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_str
                })
                
            except Exception as e:
                error_msg = f"ツール実行エラー: {str(e)}"
                logging.error(error_msg)
                print(f"\n❌ {error_msg}")
                
                # エラーもメッセージ履歴に追加（文字列として）
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f'{{"error": "{str(e)}"}}'
                })
        
        print("="*60 + "\n")
        
        # 次のターンへ（ツール結果を受けてAIが応答）
    
    else:
        # 最大ターン数に達した
        logging.warning(f"最大ターン数 {ARGS.max_turns} に達しました")
    
    # 最終的なアシスタントの応答を取得
    final_response = current_messages[-1]["content"] if current_messages[-1]["role"] == "assistant" else ""
    
    return final_response, current_messages


async def main():
    # OpenAIクライアントの準備
    openai_client = AsyncOpenAI()
    server: Optional[MCPServerStdio] = None

    try:
        # MCPサーバ接続
        server = make_server()
        print("[起動] MCPサーバへ接続中…")
        await server.connect()

        # ツールリストを取得してOpenAI形式に変換
        mcp_tools = await server.list_tools()
        openai_tools = [mcp_tool_to_openai_function(tool) for tool in mcp_tools]
        
        logging.info("[MCPツール] %s", [t.name for t in mcp_tools])
        logging.info("[OpenAI形式に変換] %d tools", len(openai_tools))
        logging.info("[モデル] %s", ARGS.model)
        logging.info("[ドキュメント] %s", ARGS.doc_name)

        # ドキュメント準備（存在保証）
        await ensure_document(server, ARGS.doc_name)

        # システムプロンプト
        system_instructions = SYSTEM_INSTRUCTIONS_TEMPLATE.format(DOC_NAME=ARGS.doc_name)

        # メッセージ履歴
        messages = [
            {"role": "system", "content": system_instructions}
        ]

        # ウォームアップ
        print("==== FreeCAD 対話モード (OpenAI直接呼び出し版) ====")
        print("例: 『半径30mmの球を作成』『Sphere_001を半径40mmに変更』など")
        print("座標を取得: 『Sphere_001の座標を教えて』")
        print("終了: /exit")
        print()

        # 最初の一言
        print("🤖 初期化中...\n")
        messages.append({
            "role": "user",
            "content": inject_doc_name("FreeCADで人工衛星を作ってください", ARGS.doc_name)
        })
        
        _, messages = await chat_with_tools(
            openai_client,
            server,
            messages,
            openai_tools,
            ARGS.model
        )

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

            # ユーザーメッセージを追加
            messages.append({
                "role": "user",
                "content": inject_doc_name(user_text, ARGS.doc_name)
            })

            # 会話実行
            _, messages = await chat_with_tools(
                openai_client,
                server,
                messages,
                openai_tools,
                ARGS.model
            )

    except asyncio.CancelledError:
        logging.warning("cancelled")
        raise
    except Exception as e:
        logging.exception("fatal error: %s", e)
    finally:
        # クリーンアップ
        if server:
            try:
                await server.cleanup()
            except Exception:
                pass
        try:
            await openai_client.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())