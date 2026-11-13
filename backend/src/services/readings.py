import csv,io,math
from datetime import datetime,timezone

def parse_time(value):
 try:
  t=datetime.fromisoformat(str(value).replace("Z","+00:00"))
  if t.tzinfo is None:raise ValueError()
  return t.astimezone(timezone.utc)
 except Exception:raise ValueError("时间须为带时区的ISO8601格式")

def parse_number(row,key,index,label):
 raw=row.get(key)
 if raw is None or raw.strip()=="":return None
 try:value=float(raw)
 except Exception:raise ValueError(f"第{index}行{label}必须为数值或空值")
 if not math.isfinite(value) or value<0:raise ValueError(f"第{index}行{label}必须非负且有限")
 return value

def parse_rows(text,need_meter):
 rows=list(csv.DictReader(io.StringIO(text)))
 if not rows or len(rows)>5000:raise ValueError("CSV需1至5000行")
 header=set(rows[0])
 meter_key="meter_kwh" if "meter_kwh" in header else "kwh" if "kwh" in header else None
 required={"timestamp","output_kg","status"}|({meter_key} if need_meter else {"kwh"})
 if meter_key is None or not required.issubset(header):
  raise ValueError("累计示数CSV需含timestamp,meter_kwh(或kwh),output_kg,status" if need_meter else "CSV需1至5000行，并含timestamp,kwh,output_kg,status")
 result=[];seen=set()
 for index,row in enumerate(rows,2):
  timestamp=parse_time(row.get("timestamp")).isoformat()
  if timestamp in seen:raise ValueError(f"第{index}行时间重复（已统一UTC）")
  seen.add(timestamp)
  status=(row.get("status") or "").strip()
  if status not in ["running","stopped"]:raise ValueError(f"第{index}行状态应为running/stopped")
  result.append({"timestamp":timestamp,"status":status,"kwh":parse_number(row,meter_key if need_meter else "kwh",index,meter_key if need_meter else "kwh"),"output_kg":parse_number(row,"output_kg",index,"output_kg")})
 return result

def parse_csv(text,mode="hourly"):
 if mode=="cumulative":return convert_cumulative(parse_rows(text,need_meter=True))
 if mode!="hourly":raise ValueError("mode须为hourly或cumulative")
 return sorted(parse_rows(text,need_meter=False),key=lambda r:r["timestamp"])

# 累计示数换算：乱序记录按UTC排序后，仅对相邻整小时作差，产量与状态仍属当前小时。
# 首条与缺测后首个有效示数只作基准；回退、跨小时缺口隔离后以当前值重建基准，不跨缺口分摊电量。
def convert_cumulative(records):
 result=[];baseline=None;previous=None;started=False
 for row in sorted(records,key=lambda r:r["timestamp"]):
  meter=row["kwh"];reason="";kwh=None
  if meter is None:
   reason="missing_measurement";baseline=None;previous=None
  elif baseline is None:
   reason="rebased" if started else "first_baseline";baseline=meter;previous=row["timestamp"];started=True
  elif (parse_time(row["timestamp"])-parse_time(previous)).total_seconds()!=3600:
   reason="hour_gap";baseline=meter;previous=row["timestamp"]
  elif meter<baseline:
   reason="rollback";baseline=meter;previous=row["timestamp"]
  else:
   kwh=round(meter-baseline,6);baseline=meter;previous=row["timestamp"]
  result.append({"timestamp":row["timestamp"],"kwh":kwh,"output_kg":row["output_kg"],"status":row["status"],"meter_kwh":meter,"excluded_reason":reason})
 return result

def normalize(readings,start_at,end_at):
 start=parse_time(start_at);end=parse_time(end_at);valid=[];excluded=[]
 for row in sorted(readings,key=lambda r:r["timestamp"]):
  if not start<=parse_time(row["timestamp"])<=end:continue
  reason=row.get("excluded_reason") or ("stopped" if row["status"]=="stopped" else "missing_measurement" if row["kwh"] is None or row["output_kg"] is None else "zero_output" if row["output_kg"]==0 else "")
  if reason:excluded.append({"timestamp":row["timestamp"],"reason":reason});continue
  intensity=row["kwh"]/row["output_kg"]
  if not math.isfinite(intensity):raise ValueError("归一能耗非有限，检查极小产量")
  valid.append({**row,"intensity":intensity})
 if len(valid)<8:raise ValueError("窗口内至少需要8条有效运行观测；停机、零产量与缺测已隔离")
 return valid,excluded
