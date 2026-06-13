"""浏览器自动化 — Playwright 表单填写"""
import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


# 字段名到简历数据的映射规则
FIELD_MAPPING = {
    # 姓名
    "name": ["姓名", "name", "真实姓名", "姓  名"],
    "phone": ["手机", "电话", "联系电话", "手机号", "mobile", "phone"],
    "email": ["邮箱", "电子邮箱", "email", "mail"],
    "gender": ["性别", "gender", "sex"],
    "birth_date": ["出生", "生日", "birth", "birthday"],
    "ethnicity": ["民族", "ethnicity"],
    "political_status": ["政治面貌", "政治", "political"],
    "hometown": ["籍贯", "户籍", "家乡", "hometown"],
    "current_city": ["现居", "所在城市", "居住地", "city"],
    "current_address": ["详细地址", "通讯地址", "address"],
    "wechat": ["微信", "wechat"],
    "qq": ["qq"],
    "university": ["学校", "院校", "毕业院校", "university", "school"],
    "major": ["专业", "major"],
    "degree": ["学历", "学位", "degree"],
    "gpa": ["绩点", "gpa", "成绩"],
    "ranking": ["排名", "ranking"],
    "target_position": ["期望岗位", "意向岗位", "应聘岗位", "position"],
    "expected_salary": ["期望薪资", "薪资", "salary"],
    "self_intro": ["自我介绍", "自我评价", "个人介绍", "简介"],
}


async def fill_form(url: str, profile_data: dict, dry_run: bool = True):
    """打开浏览器并自动填写表单
    
    Args:
        url: 投递页面 URL
        profile_data: 个人信息字典
        dry_run: True=填写后暂停等待确认, False=自动提交
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # 获取所有可填写的输入框
        inputs = await page.query_selector_all("input, select, textarea")
        filled_count = 0

        for inp in inputs:
            inp_type = await inp.get_attribute("type") or ""
            inp_name = await inp.get_attribute("name") or ""
            inp_id = await inp.get_attribute("id") or ""
            inp_placeholder = await inp.get_attribute("placeholder") or ""
            inp_label = await inp.evaluate("""el => {
                const label = el.closest('label') || document.querySelector(`label[for="${el.id}"]`);
                return label ? label.textContent.trim() : '';
            }""")

            # 跳过隐藏字段和按钮
            if inp_type in ("hidden", "submit", "button", "image"):
                continue

            # 匹配字段
            search_text = f"{inp_name} {inp_id} {inp_placeholder} {inp_label}".lower()
            matched_value = None

            for field_key, keywords in FIELD_MAPPING.items():
                for kw in keywords:
                    if kw.lower() in search_text:
                        matched_value = profile_data.get(field_key, "")
                        break
                if matched_value:
                    break

            if not matched_value:
                continue

            try:
                tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                if tag == "select":
                    # 下拉框：尝试选择匹配的选项
                    options = await inp.evaluate("""el => {
                        return Array.from(el.options).map(o => ({value: o.value, text: o.textContent.trim()}))
                    }""")
                    for opt in options:
                        if matched_value in opt["text"] or opt["text"] in matched_value:
                            await inp.select_option(value=opt["value"])
                            filled_count += 1
                            break
                elif inp_type == "radio":
                    # 单选框
                    radio_val = await inp.get_attribute("value") or ""
                    if matched_value in radio_val or radio_val in matched_value:
                        await inp.check()
                        filled_count += 1
                else:
                    # 文本输入
                    await inp.fill(matched_value)
                    filled_count += 1
            except Exception:
                continue

        print(f"已自动填写 {filled_count} 个字段")

        if dry_run:
            print("⏸️ 表单填写完成，请在浏览器中检查并手动提交")
            input("按回车关闭浏览器...")
        else:
            # 尝试点击提交按钮
            submit_btn = await page.query_selector('button[type="submit"], input[type="submit"], .submit-btn, .btn-submit')
            if submit_btn:
                await submit_btn.click()
                await page.wait_for_timeout(3000)
                print("✅ 已提交")
            else:
                print("⚠️ 未找到提交按钮，请手动提交")

        await browser.close()


async def preview_form(url: str):
    """预览表单字段（不填写）"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        inputs = await page.query_selector_all("input, select, textarea")
        fields = []
        for inp in inputs:
            inp_type = await inp.get_attribute("type") or ""
            if inp_type in ("hidden", "submit", "button", "image"):
                continue
            name = await inp.get_attribute("name") or ""
            placeholder = await inp.get_attribute("placeholder") or ""
            label = await inp.evaluate("""el => {
                const l = el.closest('label') || document.querySelector(`label[for="${el.id}"]`);
                return l ? l.textContent.trim() : '';
            }""")
            fields.append({"name": name, "placeholder": placeholder, "label": label, "type": inp_type})

        await browser.close()
        return fields


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python autofill.py <url> [--auto]")
        sys.exit(1)
    url = sys.argv[1]
    auto = "--auto" in sys.argv
    profile = json.loads(Path("data/export.json").read_text()) if Path("data/export.json").exists() else {}
    asyncio.run(fill_form(url, profile.get("profile", {}), dry_run=not auto))
