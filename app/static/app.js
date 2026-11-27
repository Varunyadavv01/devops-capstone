"use strict";

const get = (selector) => document.querySelector(selector);
const labels = { pending: "Pending", in_progress: "In progress", completed: "Completed" };
const priorityLabels = { low: "Low", medium: "Medium", high: "High" };
const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium" });
const addButton = get("#add-task");
const filterButtons = [...document.querySelectorAll("[data-filter]")];
const taskDialog = get("#task-dialog");
const deleteDialog = get("#delete-dialog");
const taskForm = get("#task-form");
const deleteForm = get("#delete-form");
let activeFilter = "";
let refreshSequence = 0;
let selectedTask = null;

async function api(url, { method = "GET", data } = {}) {
  const response = await fetch(url, {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
    cache: "no-store",
  });
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) throw new Error(body.error?.message || "The request could not be completed.");
  return body;
}

function openDialog(dialog, task) {
  selectedTask = task;
  dialog.querySelector(".form-error").hidden = true;
  if (dialog === taskDialog) {
    taskForm.reset();
    get("#dialog-title").textContent = task ? "Edit task" : "Add task";
    if (task) {
      for (const field of ["title", "description", "status", "priority"]) {
        taskForm.elements.namedItem(field).value = task[field];
      }
    }
  } else {
    get("#delete-message").textContent = `Delete “${task.title}”? This action is permanent.`;
  }
  dialog.showModal();
}

function renderTasks(tasks) {
  const template = get("#task-row");
  const rows = tasks.map((task) => {
    const row = template.content.firstElementChild.cloneNode(true);
    row.dataset.taskId = task.id;
    row.querySelector(".task-title").textContent = task.title;
    const description = row.querySelector(".task-description");
    description.textContent = task.description;
    description.hidden = !task.description;
    const badge = row.querySelector(".badge");
    badge.dataset.status = task.status;
    badge.textContent = labels[task.status];
    const priority = row.querySelector(".priority");
    priority.dataset.priority = task.priority;
    priority.textContent = priorityLabels[task.priority];
    const updated = row.querySelector("time");
    updated.dateTime = task.updated_at;
    updated.textContent = dateFormat.format(new Date(task.updated_at));
    for (const [action, dialog] of [["Edit", taskDialog], ["Delete", deleteDialog]]) {
      const control = row.querySelector(`.${action.toLowerCase()}`);
      control.title = action;
      control.setAttribute("aria-label", `${action} ${task.title}`);
      control.addEventListener("click", () => openDialog(dialog, task));
    }
    return row;
  });
  get("#task-rows").replaceChildren(...rows);
  const empty = get("#empty");
  empty.textContent = activeFilter ? "No tasks match this status." : "No tasks yet. Add a task to get started.";
  empty.hidden = tasks.length > 0;
  get("#task-table").hidden = tasks.length === 0;
  const count = get("#task-count");
  count.textContent = `${tasks.length} ${tasks.length === 1 ? "task" : "tasks"}`;
  count.hidden = tasks.length === 0;
}

async function refreshTasks() {
  const sequence = ++refreshSequence;
  const query = activeFilter ? `?status=${encodeURIComponent(activeFilter)}` : "";
  const notice = get("#notice");
  try {
    const [{ tasks }, stats] = await Promise.all([api(`/api/tasks${query}`), api("/api/stats")]);
    if (sequence !== refreshSequence) return;
    for (const key of ["total", "pending", "in_progress", "completed"]) {
      get(`#stat-${key}`).textContent = stats[key];
    }
    renderTasks(tasks);
    notice.hidden = true;
  } catch {
    if (sequence !== refreshSequence) return;
    get("#task-table").hidden = true;
    get("#empty").hidden = true;
    get("#task-count").hidden = true;
    for (const key of ["total", "pending", "in_progress", "completed"]) {
      get(`#stat-${key}`).textContent = "—";
    }
    notice.textContent = "Couldn’t load tasks. Check the backend and select a filter to retry.";
    notice.hidden = false;
  }
}

async function refreshHealth() {
  const health = get("#health");
  let ready;
  try {
    ready = (await api("/health/ready")).status === "ready";
  } catch {
    ready = false;
  }
  const state = ready ? "ready" : "unavailable";
  if (health.dataset.state !== state) {
    health.dataset.state = state;
    health.textContent = ready ? "Backend ready" : "Backend unavailable";
  }
}

function setFilter(button) {
  activeFilter = button.dataset.filter;
  for (const filter of filterButtons) filter.setAttribute("aria-pressed", String(filter === button));
}

function handleSubmit(dialog, form, request) {
  const buttons = [...form.querySelectorAll("button")];
  const error = form.querySelector(".form-error");
  dialog.querySelector(".cancel").addEventListener("click", () => dialog.close());
  dialog.addEventListener("cancel", (event) => {
    if (buttons[0].disabled) event.preventDefault();
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (buttons[0].disabled) return;
    error.hidden = true;
    for (const button of buttons) button.disabled = true;
    const task = selectedTask;
    try {
      await request(task);
      const filter = task ? filterButtons.find((button) => button.dataset.filter === activeFilter) : filterButtons[0];
      if (!task) setFilter(filter);
      dialog.close();
      const updating = refreshTasks();
      // Keep focus on a stable control while task rows are replaced.
      (task ? filter : addButton).focus();
      await updating;
    } catch (failure) {
      error.textContent = failure.message === "Failed to fetch" ? "Unable to reach the backend." : failure.message;
      error.hidden = false;
    } finally {
      for (const button of buttons) button.disabled = false;
    }
  });
}

addButton.addEventListener("click", () => openDialog(taskDialog, null));
for (const button of filterButtons) {
  button.addEventListener("click", () => {
    setFilter(button);
    refreshTasks();
  });
}
handleSubmit(taskDialog, taskForm, (task) => api(task ? `/api/tasks/${task.id}` : "/api/tasks", {
  method: task ? "PUT" : "POST",
  data: Object.fromEntries(new FormData(taskForm)),
}));
handleSubmit(deleteDialog, deleteForm, (task) => api(`/api/tasks/${task.id}`, { method: "DELETE" }));
refreshTasks();
refreshHealth();
setInterval(refreshHealth, 30_000);
