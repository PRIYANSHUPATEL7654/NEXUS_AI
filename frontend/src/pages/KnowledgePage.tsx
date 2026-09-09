import { useCallback, useEffect, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { createImport, knowledgeApi, listImports, retryImport, uploadFile, waitForImport } from "../api/modules";
import { useAuth } from "../auth/AuthContext";
import { Busy, Empty, FieldError, Notice, Status, readableDate } from "../components/ModuleUi";
import type { ImportJob, KnowledgeDocument, KnowledgeDocumentDetail, KnowledgeSummary, KnowledgeText } from "../module-types";

const messageOf=(error:unknown)=>error instanceof ApiError||error instanceof Error?error.message:"The Knowledge request failed.";

export function KnowledgePage(){
  const {token}=useAuth();
  const [documents,setDocuments]=useState<KnowledgeDocument[]>([]),[selectedId,setSelectedId]=useState<number|null>(null);
  const [detail,setDetail]=useState<KnowledgeDocumentDetail|null>(null),[text,setText]=useState<KnowledgeText|null>(null),[summaries,setSummaries]=useState<KnowledgeSummary[]>([]);
  const [imports,setImports]=useState<ImportJob[]>([]),[search,setSearch]=useState(""),[loading,setLoading]=useState(true),[busy,setBusy]=useState(""),[error,setError]=useState(""),[success,setSuccess]=useState("");
  const [file,setFile]=useState<File|null>(null),[title,setTitle]=useState(""),[description,setDescription]=useState(""),[tags,setTags]=useState(""),[summaryType,setSummaryType]=useState("detailed");

  const load=useCallback(async()=>{if(!token)return;setLoading(true);setError("");try{const [docs,jobs]=await Promise.all([knowledgeApi.list(token,search),listImports(token,"knowledge")]);setDocuments(docs);setImports(jobs);setSelectedId(current=>current&&docs.some(d=>d.id===current)?current:docs[0]?.id??null);}catch(e){setError(messageOf(e));}finally{setLoading(false);}},[token,search]);
  useEffect(()=>{void load();},[load]);
  useEffect(()=>{if(!token||!selectedId){setDetail(null);setText(null);setSummaries([]);return;}let active=true;Promise.all([knowledgeApi.detail(token,selectedId),knowledgeApi.text(token,selectedId),knowledgeApi.summaries(token,selectedId)]).then(([d,t,s])=>{if(active){setDetail(d);setText(t);setSummaries(s);}}).catch(e=>active&&setError(messageOf(e)));return()=>{active=false};},[token,selectedId]);
  const flash=(value:string)=>{setSuccess(value);window.setTimeout(()=>setSuccess(""),3500)};

  async function importDocument(event:FormEvent){event.preventDefault();if(!token||!file)return;setBusy("Uploading and extracting your document…");setError("");try{const stored=await uploadFile(token,file);const created=await createImport(token,stored.id,"knowledge");const ready=await waitForImport(token,created.id,job=>setBusy(`Import status: ${job.status.replaceAll("_"," ")}…`));if(ready.status==="failed")throw new Error(ready.failure_reason||"Document extraction failed.");const document=await knowledgeApi.createFromImport(token,ready.id,{title:title.trim()||undefined,description:description.trim()||undefined,tags:tags.split(",").map(v=>v.trim()).filter(Boolean)});setFile(null);setTitle("");setDescription("");setTags("");await load();setSelectedId(document.id);flash("Document added to Knowledge.");}catch(e){setError(messageOf(e));}finally{setBusy("");}}
  async function convertExisting(job:ImportJob){if(!token)return;setBusy("Adding completed extraction to Knowledge…");setError("");try{const document=await knowledgeApi.createFromImport(token,job.id,{tags:[]});await load();setSelectedId(document.id);flash("Import added to Knowledge.");}catch(e){setError(messageOf(e));}finally{setBusy("");}}
  async function retry(job:ImportJob){if(!token)return;setBusy("Retrying extraction…");try{const restarted=await retryImport(token,job.id);await waitForImport(token,restarted.id,updated=>setBusy(`Import status: ${updated.status.replaceAll("_"," ")}…`));await load();flash("Retry finished. Review its latest status.");}catch(e){setError(messageOf(e));}finally{setBusy("");}}
  async function createSummary(){if(!token||!selectedId)return;setBusy("Creating summary…");setError("");try{await knowledgeApi.createSummary(token,selectedId,summaryType);setSummaries(await knowledgeApi.summaries(token,selectedId));flash("Summary created.");}catch(e){setError(messageOf(e));}finally{setBusy("");}}
  async function removeDocument(){if(!token||!detail||!window.confirm(`Delete “${detail.title}” from Knowledge? The shared file remains available.`))return;setBusy("Deleting document…");try{await knowledgeApi.remove(token,detail.id);setSelectedId(null);await load();flash("Knowledge document deleted.");}catch(e){setError(messageOf(e));}finally{setBusy("");}}

  return <section className="module-workspace knowledge-workspace">
    <header className="page-heading compact"><div><p className="eyebrow">NEXUS KNOWLEDGE · DAY 17</p><h1>Your document workspace</h1><p>Upload, review extracted text, create focused summaries and keep sources organized.</p></div><span className="status-pill"><i/> {documents.length} documents</span></header>
    <FieldError message={error}/>{success&&<Notice kind="success">{success}</Notice>}{busy&&<Busy label={busy}/>}
    <div className="workspace-grid">
      <aside className="panel workspace-sidebar">
        <div className="panel-heading"><h2>Library</h2><button className="icon-button" onClick={()=>void load()} aria-label="Refresh">↻</button></div>
        <input aria-label="Search documents" placeholder="Search titles" value={search} onChange={e=>setSearch(e.target.value)}/>
        {loading?<Busy/>:documents.length===0?<Empty>No saved documents yet. Import one below.</Empty>:<div className="record-list">{documents.map(doc=><button className={selectedId===doc.id?"record-row active":"record-row"} key={doc.id} onClick={()=>setSelectedId(doc.id)}><strong>{doc.title}</strong><small>{doc.tags.length?doc.tags.join(" · "):doc.extraction_method}</small><span>{readableDate(doc.created_at)}</span></button>)}</div>}
      </aside>
      <div className="workspace-main">
        <form className="panel module-form" onSubmit={importDocument}><div className="panel-heading"><div><p className="eyebrow">NEW SOURCE</p><h2>Import a document</h2></div></div>
          <label><span>File</span><input type="file" required onChange={e=>setFile(e.target.files?.[0]||null)} accept=".pdf,.docx,.xlsx,.csv,.txt,.md,.png,.jpg,.jpeg"/></label>
          <div className="form-grid two"><label><span>Title (optional)</span><input value={title} maxLength={255} onChange={e=>setTitle(e.target.value)} placeholder="Uses filename when blank"/></label><label><span>Tags</span><input value={tags} onChange={e=>setTags(e.target.value)} placeholder="python, backend"/></label></div>
          <label><span>Description (optional)</span><textarea value={description} maxLength={2000} onChange={e=>setDescription(e.target.value)} rows={2}/></label>
          <button className="primary-button" disabled={!file||!!busy}>Upload and extract</button>
        </form>
        {detail?<div className="panel detail-panel"><div className="detail-title"><div><p className="eyebrow">SELECTED DOCUMENT</p><h2>{detail.title}</h2></div><button className="danger-button" onClick={removeDocument}>Delete</button></div>
          <div className="meta-row"><span>{detail.page_count?`${detail.page_count} page(s)`:"Page count unavailable"}</span><span>{detail.extraction_method}</span><span>{text?.character_count.toLocaleString()||0} characters</span></div>
          {detail.description&&<p>{detail.description}</p>}
          <details className="text-preview"><summary>View extracted text</summary><pre>{text?.text||detail.extracted_text}</pre></details>
          <div className="summary-controls"><label><span>Summary style</span><select value={summaryType} onChange={e=>setSummaryType(e.target.value)}><option value="short">Short</option><option value="detailed">Detailed</option><option value="revision_notes">Revision notes</option><option value="key_insights">Key insights</option></select></label><button className="primary-button" onClick={createSummary} disabled={!!busy}>Create summary</button></div>
          <div className="summary-list">{summaries.length===0?<Empty>No summaries yet.</Empty>:summaries.map(item=><article className="summary-card" key={item.id}><div><Status value={item.summary_type}/><small>{readableDate(item.created_at)}</small></div><p>{item.content}</p><button className="secondary-button" onClick={()=>token&&knowledgeApi.downloadSummary(token,item.id).catch(e=>setError(messageOf(e)))}>Download PDF</button></article>)}</div>
        </div>:<div className="panel"><Empty>Select a document to read it and create summaries.</Empty></div>}
        <div className="panel"><div className="panel-heading"><div><p className="eyebrow">PROCESSING</p><h2>Recent Knowledge imports</h2></div></div>{imports.length===0?<Empty>No import jobs yet.</Empty>:<div className="compact-list">{imports.slice(0,8).map(job=><div key={job.id}><div><strong>Import from {documents.find(d=>d.import_job_id===job.id)?.title||`uploaded file`}</strong><small>{job.extraction_method||"Waiting for extraction"}</small>{job.warnings.map(w=><em key={w}>{w}</em>)}{job.failure_reason&&<em>{job.failure_reason}</em>}</div><Status value={job.status}/>{job.status==="failed"&&<button className="secondary-button" onClick={()=>void retry(job)}>Retry</button>}{job.status==="awaiting_review"&&!documents.some(d=>d.import_job_id===job.id)&&<button className="secondary-button" onClick={()=>void convertExisting(job)}>Add to Knowledge</button>}</div>)}</div>}</div>
      </div>
    </div>
  </section>;
}
