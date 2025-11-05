#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import json
import logging
import shutil
import base64
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents.mcp import MCPServerStdio

load_dotenv()

import argparse
from PIL import Image
import numpy as np
import sys

# Windowsの旧環境対策（入っていれば自動で有効化）
try:
    import colorama
    colorama.just_fix_windows_console()
except Exception:
    pass

ASCII_CHARS = "@%#*+=-:. "  # 暗→明（好みで変更可）

def print_color_ascii(image_path, width=200, line_scale=0.55, charset=ASCII_CHARS):
    img = Image.open(image_path).convert("RGB")
    aspect = img.height / img.width
    h = max(1, int(width * aspect * line_scale))     # 文字の縦横比補正
    img = img.resize((width, h), Image.Resampling.BICUBIC)

    arr = np.array(img)                              # (H, W, 3)
    # 輝度で使用文字を選ぶ
    lum = (0.299*arr[...,0] + 0.587*arr[...,1] + 0.114*arr[...,2]).astype("uint8")
    idx = (lum * ((len(charset)-1)/255)).astype(int)

    reset = "\x1b[0m"
    out = []
    for y in range(arr.shape[0]):
        row = []
        for x in range(arr.shape[1]):
            r, g, b = map(int, arr[y, x])
            ch = charset[idx[y, x]]
            row.append(f"\x1b[38;2;{r};{g};{b}m{ch}")  # 24bit前景色
        out.append("".join(row) + reset)
    print("\n".join(out))


width = 100
image = "./b.png"    
line_scale = 0.55

    
print_color_ascii(image, width, line_scale)

def parse_args():
    p = argparse.ArgumentParser(description="FreeCAD MCP + OpenAI 直接呼び出しREPL")
    # p.add_argument("--model", default="gpt-4o", help="使用するOpenAIモデル（例: gpt-4o, gpt-4o-mini）")
    # p.add_argument("--model", default="gpt-o3", help="使用するOpenAIモデル（例: gpt-4o, gpt-4o-mini）")
    # p.add_argument("--model", default="gpt-4o-mini", help="使用するOpenAIモデル（例: gpt-4o, gpt-4o-mini）")
    p.add_argument("--model", default="gpt-4.1", help="使用するOpenAIモデル（例: gpt-4o, gpt-4o-mini）")
    # p.add_argument("--model", default="gpt-5-mini", help="使用するOpenAIモデル（例: gpt-4o, gpt-4o-mini）")
    # p.add_argument("--model", default="gpt-5", help="使用するOpenAIモデル（例: gpt-4o, gpt-4o-mini）")
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

【3Dプリンターで印刷するために必ず次のことを守ってください。】
・3㎝x3㎝x3㎝に模型が収まること
・必ず幅や厚さが5㎜以上あること
・すべてのパーツがくっついていること
・z軸正方向が上を表します
doc_name={DOC_NAME}を使用すること

【重要】ツール結果の扱い:
- すべてのツール呼び出しは成功します
- get_object, get_objects などの結果を正確に読み取ってください
- 座標、寸法、プロパティ情報を具体的に報告してください
- [画像生成済み]というマーカーがある場合、視覚的な確認が行われたことを意味します

各ターンで行うこと:
1) 実行計画(簡潔)
2) 実行するMCPツール呼び出し（作成/編集の対象名・寸法）
3) ツール結果の詳細な報告（座標、寸法など具体的な数値）
4) 生成/変更したオブジェクト名の一覧

前の会話で作成したオブジェクトを覚えており、それらを参照・編集できます。
""".strip()


class ImageStore:
    """画像データを保存・管理するクラス"""
    def __init__(self):
        self.images = {}
        self.counter = 0
    
    def add(self, image_data: str) -> str:
        """画像を保存してIDを返す"""
        self.counter += 1
        img_id = f"img_{self.counter}"
        self.images[img_id] = image_data
        return img_id
    
    def get(self, img_id: str) -> Optional[str]:
        """IDから画像データを取得"""
        return self.images.get(img_id)
    
    def clear(self):
        """全画像をクリア"""
        self.images.clear()
        self.counter = 0


# グローバル画像ストレージ
image_store = ImageStore()


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
        client_session_timeout_seconds=60,
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


def extract_content_from_tool_result(result) -> tuple[str, Optional[str]]:
    """
    ツール結果からテキストと画像を抽出
    Returns: (text_content, base64_image_data)
    """
    text_parts = []
    image_data = None
    
    if hasattr(result, 'content'):
        for item in result.content:
            if hasattr(item, 'type'):
                if item.type == 'text':
                    text_parts.append(item.text)
                elif item.type == 'image' and hasattr(item, 'data'):
                    # Base64エンコードされた画像データを保存
                    image_data = item.data
    
    text_content = '\n'.join(text_parts) if text_parts else json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)
    
    return text_content, image_data


def format_tool_result_for_display(result) -> str:
    """ツール結果を表示用にフォーマット"""
    text, has_image = extract_content_from_tool_result(result)
    if has_image:
        return text + "\n[画像データあり]"
    return text


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
        assistant_dict = {
            "role": "assistant",
            "content": assistant_message.content,
        }
        if assistant_message.tool_calls:
            assistant_dict["tool_calls"] = [tc.model_dump() for tc in assistant_message.tool_calls]
        
        current_messages.append(assistant_dict)
        
        # アシスタントの応答を表示
        if assistant_message.content:
            print(f"\n {assistant_message.content}", flush=True)
        
        # ツール呼び出しがなければ終了
        if not assistant_message.tool_calls:
            break
        
        # ツール呼び出しを処理
        print("\n" + "="*60)
        print(" ツール呼び出し")
        print("="*60)
        
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            if ARGS.show_tool_calls:
                print(f"\n {tool_name}")
                print(f"   引数: {json.dumps(tool_args, ensure_ascii=False)}")
            else:
                print(f"\n {tool_name} 実行中...")
            
            # MCPサーバーでツールを実行
            try:
                tool_result = await server.call_tool(tool_name, tool_args)
                
                # テキストと画像を抽出
                text_content, image_data = extract_content_from_tool_result(tool_result)
                
                # 画像がある場合は保存してマーカーを追加
                if image_data:
                    img_id = image_store.add(image_data)
                    text_content += f"\n[画像生成済み: {img_id}]"
                    logging.debug(f"画像を保存: {img_id}")
                
                # 結果を表示
                print(f" 結果:")
                display_text = format_tool_result_for_display(tool_result)
                if len(display_text) > 500:
                    print(display_text[:500])
                    print("... (省略)")
                else:
                    print(display_text)
                
                # ツール結果をメッセージ履歴に追加
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": text_content
                })
                
            except Exception as e:
                error_msg = f"ツール実行エラー: {str(e)}"
                logging.error(error_msg)
                print(f"❌ {error_msg}")
                
                # エラーもメッセージ履歴に追加
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f'{{"error": "{str(e)}"}}'
                })
        
        print("="*60)
        
        # 次のターンへ（ツール結果を受けてAIが応答）
    
    else:
        # 最大ターン数に達した
        logging.warning(f"最大ターン数 {ARGS.max_turns} に達しました")
    
    # 最終的なアシスタントの応答を取得
    final_response = ""
    for msg in reversed(current_messages):
        if msg["role"] == "assistant" and msg.get("content"):
            final_response = msg["content"]
            break
    
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

        # メッセージ履歴（会話全体を通して保持）
        messages = [
            {"role": "system", "content": system_instructions}
        ]

        # ウォームアップ
        print("==== FreeCAD 対話モード (OpenAI直接呼び出し版) ====")
        print("例: 『半径30mmの球を作成』『Sphere_001を半径40mmに変更』など")
        print("座標を取得: 『Sphere_001の座標を教えて』")
        print("履歴リセット: /reset")
        print("履歴確認: /history")
        print("終了: /exit")
        print()

        # 最初の一言
        print(" 初期化中...\n")
        first_message = "(必ず全MCPツール引数に doc_name='Main' を含め、寸法はmmで明示してください)\nFreeCADで人工衛星を作ってください。必ずどんなものがどこに配置されるか考えてから作業を始めてください。"
        messages.append({
            "role": "user",
            "content": first_message
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
                user_text = input("\n💬 > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[終了要求]")
                break

            if not user_text:
                continue
            if user_text.lower() in ("/exit", "exit", "quit", "/q"):
                break
            if user_text.lower() == "/reset":
                print("会話履歴をリセットしました")
                messages = [
                    {"role": "system", "content": system_instructions}
                ]
                image_store.clear()
                continue
            if user_text.lower() == "/history":
                print(f" 現在の会話履歴: {len(messages)} メッセージ")
                print(f" 保存された画像: {image_store.counter} 枚")
                for i, msg in enumerate(messages[-10:]):  # 最後の10メッセージを表示
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        if len(content) > 100:
                            content = content[:100] + "..."
                    else:
                        content = "[複合コンテンツ]"
                    print(f"  [{i}] {role}: {content}")
                continue

            # ユーザーメッセージを追加
            messages.append({
                "role": "user",
                "content": user_text
            })

            # 会話実行（messagesは更新される）
            _, messages = await chat_with_tools(
                openai_client,
                server,
                messages,
                openai_tools,
                ARGS.model
            )

            # デバッグ情報
            logging.debug(f"会話履歴長: {len(messages)} メッセージ")

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