import os

base = r"C:\Users\ynaka\study_planner"
app_path = os.path.join(base, "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''        student_name = row["name"] if row else student_id
        os.makedirs("plan_archives", exist_ok=True)
        output_path = os.path.join(
            "plan_archives", f"計画表_{student_name}_{target_date}.xlsx")
        export_excel(target_date, output_path,
                     student_id=student_id, start_date=start_date,
                     subject_filter=subject_filter if subject_filter else None)'''

new = '''        student_name = row["name"] if row else student_id
        os.makedirs("plan_archives", exist_ok=True)
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%H%M%S")
        output_path = os.path.join(
            "plan_archives", f"計画表_{student_name}_{target_date}_{ts}.xlsx")
        export_excel(target_date, output_path,
                     student_id=student_id, start_date=start_date,
                     subject_filter=subject_filter if subject_filter else None)'''

if old in content:
    content = content.replace(old, new)
    print("✅ export関数を修正しました")
else:
    print("❌ export関数が見つかりません")

# PDF出力も同様に修正
old_pdf = '''    output_path = os.path.join(
        "plan_archives", f"計画表_{student_name}_{target_date}.pdf")'''

new_pdf = '''    from datetime import datetime as _dt
    ts = _dt.now().strftime("%H%M%S")
    output_path = os.path.join(
        "plan_archives", f"計画表_{student_name}_{target_date}_{ts}.pdf")'''

if old_pdf in content:
    content = content.replace(old_pdf, new_pdf)
    print("✅ export_pdf関数を修正しました")
else:
    print("❌ export_pdf関数が見つかりません")

# MCPのgenerate_excel_planも同様に修正
old_mcp_excel = '''        output_path = os.path.join(
            archive_dir, f"計画表_{student_name}_{target_date}.xlsx")'''

new_mcp_excel = '''        from datetime import datetime as _dt2
        ts2 = _dt2.now().strftime("%H%M%S")
        output_path = os.path.join(
            archive_dir, f"計画表_{student_name}_{target_date}_{ts2}.xlsx")'''

if old_mcp_excel in content:
    content = content.replace(old_mcp_excel, new_mcp_excel)
    print("✅ app.pyのMCP Excel部分を修正しました")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

# mcp_server.pyも修正
mcp_path = os.path.join(base, "mcp_server.py")
with open(mcp_path, "r", encoding="utf-8") as f:
    mcp = f.read()

old_mcp = '''        output_path = os.path.join(
            archive_dir, f"計画表_{student_name}_{target_date}.xlsx")'''
new_mcp = '''        from datetime import datetime as _dt
        ts = _dt.now().strftime("%H%M%S")
        output_path = os.path.join(
            archive_dir, f"計画表_{student_name}_{target_date}_{ts}.xlsx")'''

if old_mcp in mcp:
    mcp = mcp.replace(old_mcp, new_mcp)
    print("✅ mcp_server.pyのExcel部分を修正しました")

old_mcp_pdf = '''        output_path = os.path.join(
            archive_dir, f"計画表_{student_name}_{target_date}.pdf")'''
new_mcp_pdf = '''        from datetime import datetime as _dt
        ts = _dt.now().strftime("%H%M%S")
        output_path = os.path.join(
            archive_dir, f"計画表_{student_name}_{target_date}_{ts}.pdf")'''

if old_mcp_pdf in mcp:
    mcp = mcp.replace(old_mcp_pdf, new_mcp_pdf)
    print("✅ mcp_server.pyのPDF部分を修正しました")

with open(mcp_path, "w", encoding="utf-8") as f:
    f.write(mcp)

print("✅ 完了")