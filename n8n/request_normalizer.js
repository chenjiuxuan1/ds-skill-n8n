const raw = $json.body ?? $json;

const FORBIDDEN_ACTION_ALIASES = new Set([
  'delete_project',
  'remove_project',
  'drop_project',
  'delete_workflow',
  'remove_workflow',
  'drop_workflow',
]);

const COUNTRIES = new Set(['cn', 'ine', 'mx', 'ph', 'pk', 'th']);
const ACTIONS = new Set([
  'list_projects',
  'list_workflows',
  'get_workflow',
  'online_workflow',
  'offline_workflow',
  'trigger_workflow',
  'list_instances',
  'get_instance',
  'retry_instance',
  'append_task',
  'append_sql_task',
  'append_shell_task',
  'disable_tasks_except',
  'disable_task',
  'delete_task',
  'dump_workflow_graph',
]);

const source = raw.source || 'codex-skill';
const country = String(raw.country || '').trim().toLowerCase();
const action = String(raw.action || '').trim();
const ds_token = String(raw.ds_token || '').trim();
const request_id = String(raw.request_id || '').trim();
const inputPayload = raw.payload && typeof raw.payload === 'object' ? raw.payload : {};

const payload = {
  project_code: inputPayload.project_code || '',
  workflow_code: inputPayload.workflow_code || '',
  workflow_name: inputPayload.workflow_name || '',
  instance_id: inputPayload.instance_id || '',
  start_node_list: inputPayload.start_node_list || '',
  schedule_time: inputPayload.schedule_time || '',
  state_type: inputPayload.state_type || '',
  search_val: inputPayload.search_val || '',
  page_no: inputPayload.page_no ?? 1,
  page_size: inputPayload.page_size ?? 20,
  custom_params: inputPayload.custom_params && typeof inputPayload.custom_params === 'object'
    ? inputPayload.custom_params
    : {},
  task_type: inputPayload.task_type || '',
  task_name: inputPayload.task_name || '',
  task_description: inputPayload.task_description || '',
  template_task_name: inputPayload.template_task_name || '',
  sql: inputPayload.sql || '',
  script: inputPayload.script || '',
  sql_type: inputPayload.sql_type ?? '',
  datasource: inputPayload.datasource || '',
  environment_code: inputPayload.environment_code ?? '',
  tenant_code: inputPayload.tenant_code || '',
  upstream_task_name: inputPayload.upstream_task_name || '',
  upstream_task_code: inputPayload.upstream_task_code || '',
  task_code: inputPayload.task_code || '',
  keep_task_names: Array.isArray(inputPayload.keep_task_names) ? inputPayload.keep_task_names : [],
  keep_task_codes: Array.isArray(inputPayload.keep_task_codes) ? inputPayload.keep_task_codes : [],
  target_task_name_prefixes: Array.isArray(inputPayload.target_task_name_prefixes)
    ? inputPayload.target_task_name_prefixes
    : [],
};

if (typeof inputPayload.restore_original_state === 'boolean') {
  payload.restore_original_state = inputPayload.restore_original_state;
}
if (typeof inputPayload.auto_offline === 'boolean') {
  payload.auto_offline = inputPayload.auto_offline;
}

const errors = [];

if (FORBIDDEN_ACTION_ALIASES.has(action)) {
  errors.push(`forbidden action: ${action}. deleting projects or workflows is not allowed; only delete_task is allowed`);
}

if (!COUNTRIES.has(country)) errors.push(`unsupported country: ${country}`);
if (!ACTIONS.has(action)) errors.push(`unsupported action: ${action}`);
if (!ds_token) errors.push('ds_token is required');

if (['online_workflow', 'offline_workflow', 'trigger_workflow', 'dump_workflow_graph'].includes(action) && !payload.workflow_code) {
  errors.push(`${action} requires workflow_code`);
}
if (action === 'get_instance' && !payload.instance_id) {
  errors.push('get_instance requires instance_id');
}
if (action === 'retry_instance') {
  if (!payload.project_code) errors.push('retry_instance requires project_code');
  if (!payload.instance_id) errors.push('retry_instance requires instance_id');
}
if (action === 'get_workflow' && !payload.workflow_code && !payload.workflow_name) {
  errors.push('get_workflow requires workflow_code or workflow_name');
}

if (['append_task', 'append_sql_task', 'append_shell_task'].includes(action)) {
  if (!payload.project_code) errors.push(`${action} requires project_code`);
  if (!payload.workflow_code) errors.push(`${action} requires workflow_code`);
  if (!payload.task_name) errors.push(`${action} requires task_name`);

  let taskType = payload.task_type;
  if (action === 'append_sql_task') taskType = 'SQL';
  if (action === 'append_shell_task') taskType = 'SHELL';
  taskType = String(taskType || '').trim().toUpperCase();
  payload.task_type = taskType;

  if (!taskType && action === 'append_task') {
    errors.push('append_task requires task_type');
  }
  if (taskType && !['SQL', 'SHELL'].includes(taskType)) {
    errors.push(`unsupported task_type: ${taskType}`);
  }
  if (taskType === 'SQL' && !payload.sql) {
    errors.push(`${action} requires sql for SQL task`);
  }
  if (taskType === 'SHELL' && !payload.script) {
    errors.push(`${action} requires script for SHELL task`);
  }
}

if (action === 'delete_task') {
  if (!payload.project_code) errors.push('delete_task requires project_code');
  if (!payload.workflow_code) errors.push('delete_task requires workflow_code');
  if (!payload.task_name && !payload.task_code) {
    errors.push('delete_task requires task_name or task_code');
  }
}

if (action === 'disable_tasks_except') {
  if (!payload.project_code) errors.push('disable_tasks_except requires project_code');
  if (!payload.workflow_code) errors.push('disable_tasks_except requires workflow_code');
  if (!payload.keep_task_names.length && !payload.keep_task_codes.length) {
    errors.push('disable_tasks_except requires keep_task_names or keep_task_codes');
  }
}

if (action === 'disable_task') {
  if (!payload.project_code) errors.push('disable_task requires project_code');
  if (!payload.workflow_code) errors.push('disable_task requires workflow_code');
  if (!payload.task_name && !payload.task_code) {
    errors.push('disable_task requires task_name or task_code');
  }
}

const payload_json = JSON.stringify(payload);
const payload_b64 = Buffer.from(payload_json, 'utf8').toString('base64');

return [
  {
    json: {
      source,
      country,
      action,
      ds_token,
      request_id,
      payload,
      payload_json,
      payload_b64,
      valid: errors.length === 0,
      errors,
    },
  },
];
