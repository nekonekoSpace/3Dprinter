#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import base64
import json
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
    p.add_argument("--show-tool-calls", action="store_true", help="ツール呼び出しと結果を詳細表示")
    p.add_argument("--debug-events", action="store_true", help="すべてのストリームイベントを表示（デバッグ用）")
    p.add_argument("--non-streaming", action="store_true", help="非ストリーミングモードを使用（ツール結果表示を確実にする）")
    return p.parse_args()


ARGS = parse_args()
logging.basicConfig(level=getattr(logging, ARGS.log_level.upper(), logging.INFO))


SYSTEM_INSTRUCTIONS_TEMPLATE = """
あなたはFreeCAD MCPツールを使うCADオペレータです。
必ずミリメートル(mm)単位で寸法を明示してください。
doc_name={DOC_NAME}を使用すること

【重要】ツール結果の扱い:
- すべてのツール呼び出しは成功していると仮定してください
- get_object, get_objects などの結果は必ず正常に返ってきています
- 結果に含まれる座標、寸法、プロパティ情報を正確に読み取ってください
- 「エラーが発生した」と判断しないでください
- ツール結果が空に見えても、それはユーザー側の表示の問題であり、実際には正しいデータが返っています

【結果の報告】:
ツールを呼び出したら、その結果を以下の形式で必ず報告してください：
```
[ツール名] の結果:
- オブジェクト名: XXX
- 座標: x=XX, y=XX, z=XX
- サイズ: 幅XX, 高さXX, 奥行XX
```

各ターンで行うこと:
1) 実行計画(簡潔)
2) 実行するMCPツール呼び出し（作成/編集の対象名・寸法）
3) ツール結果の詳細な報告（座標、寸法など具体的な数値）
4) 生成/変更したオブジェクト名の一覧（今後参照するため）

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


def setup_mcp_result_logging(server: MCPServerStdio):
    """
    MCPサーバーの call_tool メソッドをラップして、
    ツール呼び出しと結果を自動的にログ出力する
    
    注意: 現在は未使用。agentsライブラリが内部でMCPサーバーを管理している場合、
    この方法では結果をキャプチャできない可能性があります。
    代わりに --non-streaming オプションを使用してください。
    """
    original_call_tool = server.call_tool
    
    async def logged_call_tool(tool_name: str, arguments: dict):
        if ARGS.show_tool_calls:
            print(f"\n[🔧 MCPツール呼び出し: {tool_name}]", flush=True)
            print(f"   引数: {json.dumps(arguments, ensure_ascii=False)}", flush=True)
        
        result = await original_call_tool(tool_name, arguments)
        
        # 結果を常に表示
        print(f"\n[📊 {tool_name} の結果]", flush=True)
        formatted = format_tool_result(result)
        if len(formatted) > 1000:
            print(formatted[:1000] + "\n... (省略)")
        else:
            print(formatted)
        print()
        
        return result
    
    server.call_tool = logged_call_tool


def inject_doc_name(user_text: str, doc_name: str) -> str:
    """
    モデルの取りこぼし対策として、各プロンプト先頭に隠し指示を付与。
    - すべてのMCPツール引数に doc_name を必ず含める
    - 寸法はmm
    """
    prefix = f"(必ず全MCPツール引数に doc_name='{doc_name}' を含め、寸法はmmで明示してください)\n"
    return prefix + user_text


def format_tool_result(result) -> str:
    """ツール結果を読みやすくフォーマット"""
    if isinstance(result, dict):
        return json.dumps(result, ensure_ascii=False, indent=2)
    elif isinstance(result, list):
        return json.dumps(result, ensure_ascii=False, indent=2)
    else:
        return str(result)


async def stream_once(agent: Agent, user_text: str, save_image_path: Optional[str] = None) -> None:
    """
    1ターン分の対話を実行し、テキストΔを逐次表示。
    画像イベント（ある場合）をBase64連結して任意保存。
    ツール呼び出しと結果も表示。
    """
    result = Runner.run_streamed(agent, user_text)
    image_bufs: list[str] = []
    tool_results = []  # ツール結果を収集
    seen_event_types = set()  # 表示されたイベントタイプを記録

    async for event in result.stream_events():
        et = getattr(event, "type", "")
        data = getattr(event, "data", None)
        
        # すべてのイベントタイプを記録
        seen_event_types.add(et)

        # デバッグ: すべてのイベントタイプをログ出力（--log-level DEBUG 時のみ）
        if ARGS.log_level.upper() == "DEBUG":
            logging.debug(f"Event type: {et}, data type: {type(data).__name__}")

        # --debug-events モード: すべてのイベントを詳細表示
        if ARGS.debug_events:
            print(f"\n[DEBUG EVENT] type={et}", flush=True)
            if data is not None:
                # dataの属性をすべて表示
                data_dict = {}
                for attr in dir(data):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(data, attr)
                            if not callable(val):
                                data_dict[attr] = val
                        except:
                            pass
                if data_dict:
                    print(f"  data attributes: {json.dumps(data_dict, default=str, ensure_ascii=False, indent=2)}")
            print()

        # --- テキストΔ（イベント名はSDKにより揺れるため幅広く対応） ---
        if et in ("raw_response_event", "response.output_text.delta", "response.text.delta"):
            delta = None
            if isinstance(data, ResponseTextDeltaEvent):
                delta = data.delta
            else:
                delta = getattr(data, "delta", None) or getattr(data, "text", None)
            if isinstance(delta, str):
                print(delta, end="", flush=True)

        # --- ツール呼び出し開始 ---
        elif et in ("tool_call.start", "response.function_call_arguments.delta"):
            if ARGS.show_tool_calls:
                tool_name = getattr(data, "name", None) or getattr(data, "function_name", "unknown")
                print(f"\n[🔧 ツール呼び出し: {tool_name}]", flush=True)

        # --- ツール呼び出し完了（引数表示） ---
        elif et in ("tool_call.completed", "response.function_call_arguments.done"):
            if ARGS.show_tool_calls:
                tool_name = getattr(data, "name", None) or getattr(data, "function_name", "unknown")
                args = getattr(data, "arguments", None) or getattr(data, "args", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        pass
                print(f"  引数: {json.dumps(args, ensure_ascii=False)}", flush=True)

        # --- ツール結果（複数パターンに対応） ---
        # より広範なイベントタイプをチェック
        if any(keyword in et.lower() for keyword in ["tool", "result", "mcp", "function"]):
            # イベント全体を探索してツール結果を見つける
            tool_name = (getattr(data, "name", None) or 
                        getattr(data, "tool_name", None) or
                        getattr(data, "function_name", None) or
                        getattr(event, "name", None) or
                        "unknown")
            
            tool_result = (getattr(data, "result", None) or 
                          getattr(data, "content", None) or
                          getattr(data, "output", None) or
                          getattr(event, "result", None))
            
            if tool_result is not None and tool_name != "unknown":
                tool_results.append({"tool": tool_name, "result": tool_result})
                
                # 結果を常に表示（座標取得などの重要データのため）
                print(f"\n\n[📊 {tool_name} の結果]", flush=True)
                formatted = format_tool_result(tool_result)
                # 長すぎる場合は省略
                if len(formatted) > 1000:
                    print(formatted[:1000] + "\n... (省略)")
                else:
                    print(formatted)
                print()

        # --- 画像Δ（Base64） ---
        elif et in ("response.output_image.delta", "response.image.delta", "raw_response_event_image"):
            delta = getattr(data, "delta", None) or getattr(data, "b64_json", "")
            if isinstance(delta, str):
                image_bufs.append(delta)

        # --- 完了時 ---
        elif et in ("response.completed", "stream.end"):
            # ツール結果が1つもキャッチできていない場合は警告と診断情報
            if not tool_results:
                logging.warning("⚠️ ツール結果が検出されませんでした")
                logging.warning(f"検出されたイベントタイプ: {sorted(seen_event_types)}")
                logging.warning("対処法: --debug-events オプションでイベント構造を確認してください")
            
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


async def run_once_non_streaming(agent: Agent, user_text: str) -> None:
    """
    非ストリーミング版: ツール結果を確実に表示するための代替実装
    --non-streaming モード時に使用される
    """
    try:
        # 非ストリーミングで実行
        result = await Runner.run(agent, user_text)
        
        # Runnerの結果を詳しく調べる
        logging.debug(f"Result type: {type(result)}")
        logging.debug(f"Result attributes: {dir(result)}")
        
        # 応答テキストを表示
        response_text = None
        if hasattr(result, 'response'):
            resp = result.response
            if hasattr(resp, 'content'):
                content = resp.content
                if isinstance(content, list):
                    for item in content:
                        if hasattr(item, 'text'):
                            response_text = item.text
                            print(item.text)
                        elif isinstance(item, dict) and 'text' in item:
                            response_text = item['text']
                            print(item['text'])
                elif isinstance(content, str):
                    response_text = content
                    print(content)
        
        # ツール呼び出し履歴を探す（複数の属性を試行）
        tool_calls = None
        for attr in ['tool_calls', 'calls', 'function_calls', 'mcp_calls']:
            if hasattr(result, attr):
                tool_calls = getattr(result, attr)
                if tool_calls:
                    break
        
        # ツール結果を表示
        if tool_calls:
            print("\n" + "="*50)
            print("[ツール呼び出し詳細]")
            print("="*50)
            for i, call in enumerate(tool_calls, 1):
                tool_name = getattr(call, 'name', getattr(call, 'tool_name', 'unknown'))
                args = getattr(call, 'arguments', getattr(call, 'args', {}))
                result_data = getattr(call, 'result', getattr(call, 'output', None))
                
                print(f"\n{i}. {tool_name}")
                print(f"   引数: {json.dumps(args, ensure_ascii=False)}")
                if result_data:
                    print(f"   結果:")
                    formatted = format_tool_result(result_data)
                    if len(formatted) > 800:
                        lines = formatted.split('\n')
                        print('\n'.join(lines[:20]))
                        print(f"   ... ({len(lines) - 20} 行省略)")
                    else:
                        print(f"   {formatted}")
            print("="*50 + "\n")
        else:
            logging.info("ツール呼び出し情報が見つかりませんでした")
            # 結果オブジェクトの構造を表示（デバッグ用）
            if ARGS.log_level.upper() == "DEBUG":
                print("\n[DEBUG] Result構造:")
                for attr in dir(result):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(result, attr)
                            if not callable(val):
                                print(f"  {attr}: {type(val).__name__}")
                        except:
                            pass
        
        print()
        
    except Exception as e:
        logging.error(f"非ストリーミング実行エラー: {e}")
        import traceback
        traceback.print_exc()
        raise


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
        print("座標を取得したい場合: 『Sphere_001の座標を教えて』『すべてのオブジェクトの位置を表示』など")
        print("終了するには: /exit")
        print("※ツール呼び出し詳細を表示: --show-tool-calls")
        print("※すべてのイベントを表示: --debug-events")
        if ARGS.non_streaming:
            print("※非ストリーミングモードで実行中（ツール結果の表示を確実にするため）")
        print()

        # 最初の一言（人工衛星：typo修正済み）
        if ARGS.non_streaming:
            await run_once_non_streaming(agent, inject_doc_name("FreeCADで人工衛星を作ってください", ARGS.doc_name))
        else:
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

            if ARGS.non_streaming:
                await run_once_non_streaming(agent, inject_doc_name(user_text, ARGS.doc_name))
            else:
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