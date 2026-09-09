export type ProcessingStatus = "uploaded" | "extracting" | "parsing" | "awaiting_review" | "completed" | "failed";
export type StoredFile = { id:number; original_filename:string; content_type:string; extension:string; size_bytes:number; processing_status:ProcessingStatus; failure_reason:string|null; created_at:string };
export type ImportJob = { id:number; file_id:number; target_module:"knowledge"|"money"|"work"; status:ProcessingStatus; extraction_method:string|null; extracted_item_count:number; page_count:number|null; warnings:string[]; failure_reason:string|null; created_at:string; updated_at:string };

export type KnowledgeDocument = { id:number; file_id:number|null; import_job_id:number|null; title:string; description:string|null; tags:string[]; extraction_method:string; page_count:number|null; created_at:string; updated_at:string };
export type KnowledgeDocumentDetail = KnowledgeDocument & { extracted_text:string };
export type KnowledgeText = { document_id:number; text:string; character_count:number };
export type KnowledgeSummary = { id:number; document_id:number; summary_type:"short"|"detailed"|"revision_notes"|"key_insights"; content:string; generation_method:string; created_at:string };

export type GoalStatus = "active"|"paused"|"completed";
export type TopicStatus = "not_started"|"in_progress"|"mastered";
export type LearningGoal = { id:number; title:string; description:string|null; target_date:string|null; status:GoalStatus; priority:number; created_at:string; updated_at:string };
export type LearningTopic = { id:number; goal_id:number; source_document_id:number|null; title:string; description:string|null; current_level:number; target_level:number; status:TopicStatus; created_at:string; updated_at:string };
export type ProgressEntry = { id:number; topic_id:number; progress_percent:number; study_minutes:number; notes:string|null; recorded_at:string };
export type SkillGap = { topic_id:number; topic_title:string; current_level:number; target_level:number; gap:number; recommended_action:string };
export type QuizReadyDocument = { document_id:number; title:string; character_count:number; sentence_count:number; keyword_count:number; quiz_ready:boolean; reason:string };
export type QuizReadiness = QuizReadyDocument & { topic_id:number; topic_title:string };
export type QuizQuestion = { id:number; topic_id:number; question:string; options:string[]; generation_method:string; created_at:string };
export type QuizAnswer = { attempt_id:number; question_id:number; selected_option_index:number; correct_option_index:number; is_correct:boolean; explanation:string; attempted_at:string };
export type QuizScore = { topic_id:number; attempts:number; correct_answers:number; score_percent:number };

export type TransactionType = "expense"|"income";
export type MoneyCategory = "Food"|"Transport"|"Shopping"|"Bills"|"Health"|"Education"|"Entertainment"|"Housing"|"Salary"|"Transfer"|"Other";
export type MoneyTransaction = { id:number; batch_id:number|null; transaction_date:string; description:string; amount:string; transaction_type:TransactionType; category:MoneyCategory; currency:string; source:"manual"|"pasted_text"|"file"; created_at:string };
export type MoneyDraft = { id:number; batch_id:number; transaction_date:string; description:string; amount:string; transaction_type:TransactionType; category:MoneyCategory; confidence:string; warnings:string[]; source_location:string|null; possible_duplicate:boolean; duplicate_transaction_id:number|null; created_at:string };
export type MoneyBatch = { id:number; file_id:number|null; import_job_id:number|null; source_type:"pasted_text"|"file"; status:"awaiting_review"|"approved"|"cancelled"; extraction_method:string|null; default_currency:string; warnings:string[]; approved_at:string|null; created_at:string };
export type MoneyBatchDetail = MoneyBatch & { raw_text_retained:boolean; drafts:MoneyDraft[] };
export type MoneyAnalytics = { date_from:string|null; date_to:string|null; currency:string; income_total:string; expense_total:string; net_total:string; transaction_count:number; category_breakdown:{category:string;total:string;transaction_count:number}[]; monthly_trend:{month:string;income:string;expenses:string;net:string}[]; largest_expenses:MoneyTransaction[] };

export type ProjectStatus = "planned"|"in_progress"|"blocked"|"completed"|"cancelled";
export type TaskStatus = "backlog"|"planned"|"in_progress"|"blocked"|"completed"|"cancelled";
export type WorkProject = { id:number; title:string; description:string|null; client_name:string|null; status:ProjectStatus; due_date:string|null; created_at:string; updated_at:string };
export type WorkTask = { id:number; project_id:number; parent_task_id:number|null; source_plan_id:number|null; title:string; description:string|null; status:TaskStatus; priority:number; complexity:number; due_date:string|null; estimated_minutes_low:number; estimated_minutes_high:number; actual_minutes:number|null; dependencies:number[]; notes:string|null; completed_at:string|null; created_at:string; updated_at:string };
export type WorkDraft = { id:number; plan_import_id:number; title:string; description:string|null; priority:number; complexity:number; due_date:string|null; estimated_minutes_low:number; estimated_minutes_high:number; confidence:string; source_location:string|null; warnings:string[]; created_at:string };
export type WorkPlan = { id:number; project_id:number|null; file_id:number|null; import_job_id:number|null; status:"awaiting_review"|"approved"|"cancelled"; proposed_project_title:string; extraction_method:string|null; estimated_minutes_low:number; estimated_minutes_high:number; estimate_confidence:"low"|"medium"|"high"; assumptions:string[]; warnings:string[]; approved_at:string|null; created_at:string };
export type WorkPlanDetail = WorkPlan & { drafts:WorkDraft[] };
export type WorkEstimate = { project_id:number; pending_task_count:number; estimated_minutes_low:number; estimated_minutes_high:number; completed_actual_minutes:number; assumptions:string[] };
export type WorkDashboard = { total_projects:number; active_projects:number; pending_tasks:number; blocked_tasks:number; completed_tasks:number; overdue_tasks:number; estimated_remaining_minutes_low:number; estimated_remaining_minutes_high:number };
