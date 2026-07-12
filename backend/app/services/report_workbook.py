from __future__ import annotations
import io,json
from typing import Any
import xlsxwriter  # type: ignore[import-untyped]

SHEETS=[("General Posts","general"),("Toy Family","toy_family"),("Emerging","emerging"),("Creators","creators"),("Creative Mechanisms","formats"),("Hashtags","hashtags"),("Sounds","sounds"),("Categories","product_categories"),("Hooks","hooks"),("Concepts","concepts")]
def report_xlsx(report_date:str,payload:dict[str,Any])->bytes:
    stream=io.BytesIO();book=xlsxwriter.Workbook(stream,{"in_memory":True});book.set_properties({"title":f"SignalScope - {report_date}","comments":"Observed within the monitored sample. Coverage is not exhaustive."});f=_formats(book);_summary(book,report_date,payload,f)
    for title,key in SHEETS:_records(book,title,payload.get(key,[]),f)
    _key_values(book,"Data Quality",payload.get("data_quality",{}),f);_key_values(book,"Action Plan",payload.get("actions",{}),f);_records(book,"Do Not Copy",payload.get("do_not_copy",[]),f);book.close();return stream.getvalue()
def _formats(book):
    return {"title":book.add_format({"bold":True,"font_size":22,"font_color":"#FFFFFF","bg_color":"#132B2B","valign":"vcenter"}),"section":book.add_format({"bold":True,"font_size":14,"font_color":"#132B2B","bottom":2,"bottom_color":"#0C6F69"}),"header":book.add_format({"bold":True,"font_color":"#FFFFFF","bg_color":"#0C6F69","text_wrap":True,"valign":"vcenter"}),"text":book.add_format({"font_color":"#172426","valign":"top","text_wrap":True}),"integer":book.add_format({"font_color":"#172426","valign":"top","num_format":"#,##0"}),"number":book.add_format({"font_color":"#172426","valign":"top","num_format":"#,##0.0"}),"link":book.add_format({"font_color":"#0C6F69","underline":True}),"label":book.add_format({"bold":True,"font_color":"#425A58","bg_color":"#EDF5F2","valign":"top"}),"value":book.add_format({"font_color":"#172426","text_wrap":True,"valign":"top"}),"warning":book.add_format({"font_color":"#6A5200","bg_color":"#FFF4D8","text_wrap":True,"valign":"vcenter"}),"high":book.add_format({"font_color":"#14532D","bg_color":"#DCFCE7"}),"medium":book.add_format({"font_color":"#854D0E","bg_color":"#FEF9C3"}),"low":book.add_format({"font_color":"#991B1B","bg_color":"#FEE2E2"})}
def _summary(book,date,payload,f):
    s=book.add_worksheet("Executive Summary");s.hide_gridlines(2);s.set_tab_color("#0C6F69");s.set_column("A:A",28);s.set_column("B:F",22);s.set_row(0,34);s.merge_range("A1:F1",f"SignalScope - {date}",f["title"]);s.merge_range("A2:F3","Observed within the monitored sample. Coverage is not exhaustive. Provider-reported metrics are not predictions.",f["warning"]);m=payload.get("metadata",{});kpis=[("Videos",m.get("videos")),("Creators",m.get("creators")),("Sounds",m.get("sounds")),("Hashtags",m.get("hashtags")),("Snapshots",m.get("snapshots"))];s.write("A5","REPORT COVERAGE",f["section"])
    for c,(name,value) in enumerate(kpis):s.write(5,c,name,f["header"]);s.write(6,c,value or 0,f["integer"])
    s.write("A9","EXECUTIVE SIGNALS",f["section"]);row=9
    for key,value in payload.get("executive",{}).items():s.write(row,0,_label(key),f["label"]);s.merge_range(row,1,row,5,_string(value),f["value"]);row+=1
    s.freeze_panes(4,0)
def _records(book,title,records,f):
    s=book.add_worksheet(title[:31]);s.hide_gridlines(2);rows=[x for x in records if isinstance(x,dict)] if isinstance(records,list) else []
    if not rows:s.write("A1",title,f["title"]);s.write("A3","Not available in the supplied dataset.",f["warning"]);return
    fields=[]
    for record in rows:
        for key in record:
            if key not in fields:fields.append(key)
    s.set_row(0,34);s.merge_range(0,0,0,len(fields)-1,title,f["title"]);s.write_row(2,0,[_label(x) for x in fields],f["header"]);s.set_row(2,32)
    for ri,record in enumerate(rows,3):
        for ci,field in enumerate(fields):_write(s,ri,ci,field,record.get(field),f)
    last=len(rows)+2;s.autofilter(2,0,last,len(fields)-1);s.freeze_panes(3,min(2,len(fields)))
    for ci,field in enumerate(fields):s.set_column(ci,ci,_width(field,[r.get(field) for r in rows]))
    if "confidence" in fields:
        ci=fields.index("confidence");rg=xlsxwriter.utility.xl_range(3,ci,last,ci)
        for text,fmt in [("High","high"),("Medium","medium"),("Low","low")]:s.conditional_format(rg,{"type":"text","criteria":"containing","value":text,"format":f[fmt]})
def _key_values(book,title,values,f):
    s=book.add_worksheet(title[:31]);s.hide_gridlines(2);s.set_column("A:A",34);s.set_column("B:B",90);s.merge_range("A1:B1",title,f["title"]);s.write_row("A3",["Metric","Value"],f["header"])
    for row,(key,value) in enumerate((values or {}).items(),3):s.write(row,0,_label(key),f["label"]);s.write(row,1,_string(value),f["value"])
    s.freeze_panes(3,0)
def _write(s,row,col,field,value,f):
    if value is None:s.write(row,col,"Not available",f["text"])
    elif field=="url" and isinstance(value,str):s.write_url(row,col,value,f["link"],"Open on TikTok")
    elif isinstance(value,bool):s.write_boolean(row,col,value,f["text"])
    elif isinstance(value,(int,float)):s.write_number(row,col,value,f["integer"] if isinstance(value,int) else f["number"])
    else:s.write(row,col,_string(value),f["text"])
def _width(field,values):
    if field in {"caption","trending_reason","adaptation_opportunity","structure","voiceover","material_difference"}:return 44
    if field in {"url","copyright_warning","safety_warning","hashtags","shot_list"}:return 30
    return max(11,min(max([len(_label(field))]+[len(_string(x)) for x in values[:50]])+2,24))
def _label(value):return value.replace("_"," ").title()
def _string(value):
    if value is None:return "Not available"
    if isinstance(value,(list,dict)):return json.dumps(value,ensure_ascii=False)
    return str(value)
