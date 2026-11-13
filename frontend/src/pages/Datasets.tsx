import {useState} from 'react';
import {useDatasets} from '../stores/datasets';
import {canWrite} from '../stores/auth';
import {useTask} from '../hooks/useTask';
import PageHeading from '../components/common/PageHeading';
import Notice from '../components/common/Notice';
import {exclusionLabels,sourceModeLabels} from '../constants/enums';
import {hour} from '../utils/format';

function HourlyPreview({rows}:{rows:any[]}){
 return <div className="table-wrap"><table><thead><tr><th>时间 UTC</th><th>电量 kWh</th><th>产量 kg</th><th>状态</th></tr></thead><tbody>{rows.slice(0,20).map(r=><tr key={r.timestamp}><td>{hour(r.timestamp)}</td><td>{r.kwh??'缺测'}</td><td>{r.output_kg??'缺测'}</td><td>{r.status}</td></tr>)}</tbody></table><small>前20条预览，计算使用窗口内全部观测。</small></div>;
}

function CumulativePreview({rows}:{rows:any[]}){
 return <div className="table-wrap"><table><thead><tr><th>时间 UTC</th><th>原示数 kWh</th><th>换算电量 kWh</th><th>产量 kg</th><th>状态</th><th>隔离原因</th></tr></thead><tbody>{rows.slice(0,20).map(r=><tr key={r.timestamp}><td>{hour(r.timestamp)}</td><td>{r.meter_kwh??'缺测'}</td><td>{r.kwh??'—'}</td><td>{r.output_kg??'缺测'}</td><td>{r.status}</td><td>{r.excluded_reason?exclusionLabels[r.excluded_reason]:''}</td></tr>)}</tbody></table><small>前20条预览：相邻整小时示数作差，产量属当前小时；首条、回退、缺测与跨小时缺口只作基准或隔离，不分摊电量。</small></div>;
}

export default function Datasets(){
 const data=useDatasets(),[name,setName]=useState(''),[text,setText]=useState(''),[description,setDescription]=useState(''),[selected,setSelected]=useState(''),[mode,setMode]=useState<'hourly'|'cumulative'>('hourly');
 const {error,busy,act}=useTask();
 return <><PageHeading index="01 / 电表记录" title="让每个小时，保留原始来处。" note="小时电量CSV列timestamp,kwh,output_kg,status；新电表选累计示数，列meter_kwh（兼容kwh）。带时区时间统一UTC、乱序排序，重复时刻拒绝；首条、示数回退、缺测、跨小时缺口分别隔离并保留原因。"/>
 <div className="two-col"><section><h2>观测批次</h2><Notice message={data.error}/>{data.items.map(row=><article className="dataset-row" key={row.id}><button className="record-open" onClick={()=>setSelected(selected===row.id?'':row.id)}><h3>{row.name}</h3><p>{row.readings.length}条 · {sourceModeLabels[row.source_mode||'hourly']} · {row.description}</p><span>查看原始小时记录 ↗</span></button>{selected===row.id&&(row.source_mode==='cumulative'?<CumulativePreview rows={row.readings}/>:<HourlyPreview rows={row.readings}/>)}</article>)}</section>
 {canWrite()?<form className="editor-panel" onSubmit={e=>{e.preventDefault();void act(async()=>{await data.create({name,csv_text:text,description,mode});setName('');setText('')})}}><h2>导入电表观测</h2><label>批次名称<input value={name} onChange={e=>setName(e.target.value)} minLength={2} required/></label><label>计量格式<select value={mode} onChange={e=>setMode(e.target.value as 'hourly'|'cumulative')}><option value="hourly">小时电量</option><option value="cumulative">累计示数（新电表）</option></select></label><label>CSV文件<input type="file" accept=".csv" onChange={e=>{const file=e.target.files?.[0];if(file)void file.text().then(setText)}}/></label><label>CSV内容<textarea value={text} onChange={e=>setText(e.target.value)} rows={8} required placeholder={mode==='cumulative'?'timestamp,meter_kwh,output_kg,status':'timestamp,kwh,output_kg,status'}/></label><label>计量口径<input value={description} onChange={e=>setDescription(e.target.value)}/></label><Notice message={error}/><button disabled={busy}>校验并导入</button></form>:<aside className="margin-notes">只读账号可以核查原始观测，导入需要分析师权限。</aside>}</div></>;
}
