"""
X Cookie 提取工具（手动模式）

从 Chrome 浏览器中复制两个 cookie 值，粘贴到此脚本即可。

操作步骤（看终端提示）：
    python3.11 setup_cookies.py
"""
import json


COOKIES_FILE = "cookies.json"


def main() -> None:
    print()
    print("=" * 55)
    print("  X Cookie 提取工具")
    print("=" * 55)
    print()
    print("请按以下步骤操作：")
    print()
    print("  1. 打开 Chrome 浏览器，确保已登录 x.com")
    print("  2. 访问 https://x.com/home")
    print("  3. 按 Cmd + Option + I 打开开发者工具")
    print("  4. 点击顶部的「Application」标签页")
    print("     （如果看不到，点击 >> 展开更多标签）")
    print("  5. 左侧栏找到 Cookies → 点击 https://x.com")
    print("  6. 在右侧列表中找到以下两个 cookie：")
    print()
    print("     auth_token   （一串字母数字，约40个字符）")
    print("     ct0          （一串字母数字，约160个字符）")
    print()
    print("  7. 双击 Value 列的值 → 右键复制 → 粘贴到下方")
    print()
    print("-" * 55)

    auth_token = input("请粘贴 auth_token 的值: ").strip()
    if not auth_token:
        print("错误: auth_token 不能为空")
        return

    ct0 = input("请粘贴 ct0 的值: ").strip()
    if not ct0:
        print("错误: ct0 不能为空")
        return

    cookies = {
        "auth_token": auth_token,
        "ct0": ct0,
    }

    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f, indent=2)

    print()
    print(f"Cookie 已保存到 {COOKIES_FILE}")
    print("现在可以运行: python3.11 main.py --dry-run")
    print()


if __name__ == "__main__":
    main()
