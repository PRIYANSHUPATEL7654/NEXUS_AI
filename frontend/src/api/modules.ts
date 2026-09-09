import { download, request } from "./client";
import type {
  ImportJob, KnowledgeDocument, KnowledgeDocumentDetail, KnowledgeSummary, KnowledgeText,
  LearningGoal, LearningTopic, MoneyAnalytics, MoneyBatch, MoneyBatchDetail, MoneyDraft,
  MoneyTransaction, ProgressEntry, QuizAnswer, QuizQuestion, QuizReadiness, QuizReadyDocument,
  QuizScore, SkillGap, StoredFile, WorkDashboard, WorkDraft, WorkEstimate, WorkPlan,
  WorkPlanDetail, WorkProject, WorkTask,
} from "../module-types";
import type { Notification } from "../types";

const json = (method:string, payload?:unknown):RequestInit => ({ method, body: payload === undefined ? undefined : JSON.stringify(payload) });
const query = (values:Record<string,string|number|undefined|null>) => {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key,value]) => { if (value !== undefined && value !== null && value !== "") params.set(key,String(value)); });
  const result = params.toString();
  return result ? `?${result}` : "";
};

export async function uploadFile(token:string, file:File) {
  const data = new FormData(); data.append("file", file);
  return request<StoredFile>("/files/upload", { method:"POST", body:data }, token);
}
export const createImport = (token:string,file_id:number,target_module:"knowledge"|"money"|"work") => request<ImportJob>("/imports",json("POST",{file_id,target_module}),token);
export const readImport = (token:string,id:number) => request<ImportJob>(`/imports/${id}`,{},token);
export const listImports = (token:string,target_module:"knowledge"|"money"|"work") => request<ImportJob[]>(`/imports${query({target_module,limit:100})}`,{},token);
export const retryImport = (token:string,id:number) => request<ImportJob>(`/imports/${id}/retry`,json("POST"),token);
export async function waitForImport(token:string,id:number,onUpdate:(job:ImportJob)=>void) {
  for (let attempt=0; attempt<90; attempt+=1) {
    const job=await readImport(token,id); onUpdate(job);
    if (["awaiting_review","completed","failed"].includes(job.status)) return job;
    await new Promise(resolve => window.setTimeout(resolve,1000));
  }
  throw new Error("Import is still processing. Open Recent imports to check it again.");
}

export const knowledgeApi = {
  list:(token:string,search="")=>request<KnowledgeDocument[]>(`/knowledge/documents${query({search:search.trim()||undefined,limit:100})}`,{},token),
  detail:(token:string,id:number)=>request<KnowledgeDocumentDetail>(`/knowledge/documents/${id}`,{},token),
  text:(token:string,id:number)=>request<KnowledgeText>(`/knowledge/documents/${id}/text`,{},token),
  createFromImport:(token:string,job:number,payload:{title?:string;description?:string;tags:string[]})=>request<KnowledgeDocument>(`/knowledge/documents/from-import/${job}`,json("POST",payload),token),
  remove:(token:string,id:number)=>request<void>(`/knowledge/documents/${id}`,json("DELETE"),token),
  summaries:(token:string,id:number)=>request<KnowledgeSummary[]>(`/knowledge/documents/${id}/summaries`,{},token),
  createSummary:(token:string,id:number,summary_type:string)=>request<KnowledgeSummary>(`/knowledge/documents/${id}/summaries`,json("POST",{summary_type}),token),
  downloadSummary:(token:string,id:number)=>download(`/knowledge/summaries/${id}/pdf`,token,"nexus-summary.pdf"),
};

export const learnApi = {
  goals:(token:string)=>request<LearningGoal[]>("/learn/goals",{},token),
  createGoal:(token:string,payload:unknown)=>request<LearningGoal>("/learn/goals",json("POST",payload),token),
  updateGoal:(token:string,id:number,payload:unknown)=>request<LearningGoal>(`/learn/goals/${id}`,json("PATCH",payload),token),
  deleteGoal:(token:string,id:number)=>request<void>(`/learn/goals/${id}`,json("DELETE"),token),
  topics:(token:string)=>request<LearningTopic[]>("/learn/topics",{},token),
  createTopic:(token:string,goal:number,payload:unknown)=>request<LearningTopic>(`/learn/goals/${goal}/topics`,json("POST",payload),token),
  updateTopic:(token:string,id:number,payload:unknown)=>request<LearningTopic>(`/learn/topics/${id}`,json("PATCH",payload),token),
  progress:(token:string,id:number)=>request<ProgressEntry[]>(`/learn/topics/${id}/progress`,{},token),
  addProgress:(token:string,id:number,payload:unknown)=>request<ProgressEntry>(`/learn/topics/${id}/progress`,json("POST",payload),token),
  gaps:(token:string,goal:number)=>request<SkillGap[]>(`/learn/goals/${goal}/skill-gaps`,{},token),
  readyDocuments:(token:string)=>request<QuizReadyDocument[]>("/learn/quiz-ready-documents",{},token),
  readiness:(token:string,id:number)=>request<QuizReadiness>(`/learn/topics/${id}/quiz/readiness`,{},token),
  generateQuiz:(token:string,id:number,count:number)=>request<QuizQuestion[]>(`/learn/topics/${id}/quiz/generate`,json("POST",{question_count:count}),token),
  quiz:(token:string,id:number)=>request<QuizQuestion[]>(`/learn/topics/${id}/quiz`,{},token),
  answer:(token:string,id:number,index:number)=>request<QuizAnswer>(`/learn/quiz/questions/${id}/answer`,json("POST",{selected_option_index:index}),token),
  score:(token:string,id:number)=>request<QuizScore>(`/learn/topics/${id}/quiz/score`,{},token),
};

export const moneyApi = {
  transactions:(token:string,filters:Record<string,string>)=>request<MoneyTransaction[]>(`/money/transactions${query({...filters,limit:200})}`,{},token),
  createTransaction:(token:string,payload:unknown)=>request<MoneyTransaction>("/money/transactions",json("POST",payload),token),
  deleteTransaction:(token:string,id:number)=>request<void>(`/money/transactions/${id}`,json("DELETE"),token),
  paste:(token:string,text:string,currency:string)=>request<MoneyBatchDetail>("/money/imports/pasted-text",json("POST",{text,default_currency:currency}),token),
  fromImport:(token:string,id:number,currency:string)=>request<MoneyBatchDetail>(`/money/imports/from-job/${id}`,json("POST",{default_currency:currency}),token),
  batches:(token:string)=>request<MoneyBatch[]>("/money/imports",{},token),
  batch:(token:string,id:number)=>request<MoneyBatchDetail>(`/money/imports/${id}`,{},token),
  updateDraft:(token:string,id:number,payload:unknown)=>request<MoneyDraft>(`/money/imports/drafts/${id}`,json("PATCH",payload),token),
  deleteDraft:(token:string,id:number)=>request<void>(`/money/imports/drafts/${id}`,json("DELETE"),token),
  approve:(token:string,id:number,payload:unknown)=>request<{transactions_created:number}>(`/money/imports/${id}/approve`,json("POST",payload),token),
  cancel:(token:string,id:number)=>request<MoneyBatch>(`/money/imports/${id}/cancel`,json("POST"),token),
  analytics:(token:string,currency:string,date_from="",date_to="")=>request<MoneyAnalytics>(`/money/analytics/summary${query({currency,date_from,date_to})}`,{},token),
  export:(token:string,date_from="",date_to="")=>download(`/money/transactions/export.csv${query({date_from,date_to})}`,token,"nexus-transactions.csv"),
};

export const workApi = {
  dashboard:(token:string)=>request<WorkDashboard>("/work/dashboard",{},token),
  projects:(token:string)=>request<WorkProject[]>("/work/projects",{},token),
  createProject:(token:string,payload:unknown)=>request<WorkProject>("/work/projects",json("POST",payload),token),
  updateProject:(token:string,id:number,payload:unknown)=>request<WorkProject>(`/work/projects/${id}`,json("PATCH",payload),token),
  tasks:(token:string,project_id?:number,status="")=>request<WorkTask[]>(`/work/tasks${query({project_id,status})}`,{},token),
  createTask:(token:string,project:number,payload:unknown)=>request<WorkTask>(`/work/projects/${project}/tasks`,json("POST",payload),token),
  updateTask:(token:string,id:number,payload:unknown)=>request<WorkTask>(`/work/tasks/${id}`,json("PATCH",payload),token),
  deleteTask:(token:string,id:number)=>request<void>(`/work/tasks/${id}`,json("DELETE"),token),
  estimate:(token:string,id:number)=>request<WorkEstimate>(`/work/projects/${id}/estimate`,{},token),
  plans:(token:string)=>request<WorkPlan[]>("/work/imports",{},token),
  plan:(token:string,id:number)=>request<WorkPlanDetail>(`/work/imports/${id}`,{},token),
  fromImport:(token:string,id:number,project_id:number|null,title:string)=>request<WorkPlanDetail>(`/work/imports/from-job/${id}`,json("POST",{project_id,fallback_project_title:title}),token),
  updateDraft:(token:string,id:number,payload:unknown)=>request<WorkDraft>(`/work/imports/drafts/${id}`,json("PATCH",payload),token),
  deleteDraft:(token:string,id:number)=>request<void>(`/work/imports/drafts/${id}`,json("DELETE"),token),
  approve:(token:string,id:number,create=true)=>request<{project_id:number;tasks_created:number}>(`/work/imports/${id}/approve`,json("POST",{create_project_if_missing:create}),token),
  cancel:(token:string,id:number)=>request<WorkPlan>(`/work/imports/${id}/cancel`,json("POST"),token),
};

export const notificationApi = {
  sync:(token:string)=>request<{created_count:number;unread_count:number}>("/notifications/sync",json("POST"),token),
  list:(token:string,unreadOnly=false)=>request<Notification[]>(`/notifications${query({unread_only:String(unreadOnly),limit:50})}`,{},token),
  count:(token:string)=>request<{unread_count:number}>("/notifications/unread-count",{},token),
  read:(token:string,id:number)=>request<Notification>(`/notifications/${id}/read`,json("PATCH"),token),
  readAll:(token:string)=>request<{updated_count:number}>("/notifications/read-all",json("POST"),token),
  remove:(token:string,id:number)=>request<void>(`/notifications/${id}`,json("DELETE"),token),
};
