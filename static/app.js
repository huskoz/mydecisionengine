const addTaskForm = document.getElementById('addTaskForm');
const statusMessage = document.getElementById('statusMessage');
const clearButton = document.getElementById('clearButton');

let currentEditTaskId = null;
let currentEditTaskData = null;

addTaskForm.addEventListener('submit', handleFormSubmit);
clearButton.addEventListener('click', () => handleClearForm(true));
const testScoreBtn = document.getElementById('testScoreBtn');
testScoreBtn.addEventListener('click', uiTestScore);

const generatePlanBtn = document.getElementById('generatePlanBtn');
const planResultsDiv = document.getElementById('planResults');
generatePlanBtn.addEventListener('click', uiGeneratePlan);

async function uiGeneratePlan() {
    try {
        const selectedMode = document.getElementById('modeSelect').value;

        let endpointUrl = '/plan';
        if (selectedMode !== "") {
            endpointUrl = `/plan?mode=${selectedMode}`;
        }
        const response = await fetch(endpointUrl);
        const planData = await response.json();

        planResultsDiv.innerHTML = `<h3>Active Mode: ${planData.mode}</h3>`;

        planData.tasks.forEach(item => {
            const planCard = document.createElement('div');

            const isDoNow = item.verdict === 'DO NOW';
            planCard.style.border = isDoNow ? "3px solid green" : "1px solid gray";
            planCard.style.padding = "10px";
            planCard.style.margin = "10px 0";
            planCard.style.backgroundColor = isDoNow ? "#e8f5e9" : "#f8f9fa";

            planCard.innerHTML = `
                <h3 style="margin: 0;">${item.id} (Rank: ${item.rank || 'N/A'})</h3>
                <h2 style="color: ${isDoNow ? 'green' : 'gray'};">Verdict: ${item.verdict}</h2>
                <p><strong>Score:</strong> ${item.priority_score}</p>
                <p><em>Reason: ${item.reason}</em></p>
            `;

            planResultsDiv.appendChild(planCard);
        });

    } catch (error) {
        console.error("Error generating plan:", error);
    }
}

async function uiTestScore() {
    const playerImpact = parseFloat(document.getElementById('playerImpact').value);
    const selectedMode = document.getElementById('modeSelect').value; // NEW: Grab the dropdown value!

    const signals = {
        player_impact: playerImpact || 0,
        low_effort: 3.0,
        unblocks_work: 2.0,
        rework_risk: 1.0,
        relevance: 4.0
    };

    let endpointUrl = '/evaluate';
    if (selectedMode !== "") {
        endpointUrl = `/evaluate?mode=${selectedMode}`;
    }

    try {
        const response = await fetch(endpointUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(signals)
        });

        const result = await response.json();

        if (response.ok) {
            statusMessage.innerText = `Hypothetical Score: ${result.priority_score} (Mode: ${result.mode})`;
            statusMessage.style.color = "blue";
        } else {
            statusMessage.innerText = "Error calculating score.";
        }
    } catch (error) {
        console.error("Network error:", error);
    }
}


async function handleFormSubmit(event) {
    event.preventDefault();

    const taskPayload = buildTaskPayload();

    if (currentEditTaskId === null) {
        await sendTaskToServer(taskPayload);
    } else {
        taskPayload.id = currentEditTaskId;
        await putTaskToServer(currentEditTaskId, taskPayload);
    }

    await fetchAndDisplayTasks();

    handleClearForm(false);
}

function handleClearForm(clearMessage = true) {
    addTaskForm.reset();

    if (clearMessage) {
        statusMessage.innerText = "";
    }

    currentEditTaskId = null;
    currentEditTaskData = null;

    document.getElementById('taskId').disabled = false;

    document.querySelector('#addTaskForm button[type="submit"]').innerText = "Submit Task (Soumettre)";
    document.querySelector('h1').innerText = "Add a New Task";
}

function buildTaskPayload() {
    const id = document.getElementById('taskId').value;
    const readiness = parseInt(document.getElementById('taskReadiness').value);
    const playerImpact = parseFloat(document.getElementById('playerImpact').value);

    let payload;

    if (currentEditTaskData !== null) {
        payload = JSON.parse(JSON.stringify(currentEditTaskData));
    } else {
        payload = {
            id: "",
            signals: { player_impact: 0, low_effort: 3.0, unblocks_work: 2.0, rework_risk: 1.0, relevance: 4.0 },
            readiness: 1,
            depends_on: [],
            needs: { programming: 1, music: 0, art: 0, gameplay: 0 }
        };
    }

    payload.id = id;
    payload.readiness = readiness;
    payload.signals.player_impact = playerImpact;

    return payload;
}


async function sendTaskToServer(taskData) {
    try {
        const response = await fetch('/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });

        const result = await response.json();

        if (response.ok) {
            statusMessage.innerText = "Success! Task added to config.yaml.";
            statusMessage.style.color = "green";
        } else {
            statusMessage.innerText = "Error: " + result.detail;
            statusMessage.style.color = "red";
        }
    } catch (error) {
        console.error("Network error:", error);
        statusMessage.innerText = "A network error occurred. Is the server running?";
        statusMessage.style.color = "red";
    }
}

async function putTaskToServer(taskId, taskData) {
    try {
        const response = await fetch(`/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });

        const result = await response.json();

        if (response.ok) {
            statusMessage.innerText = `Success! Task '${taskId}' fully updated.`;
            statusMessage.style.color = "green";
        } else {
            statusMessage.innerText = "Error: " + result.detail;
            statusMessage.style.color = "red";
        }
    } catch (error) {
        console.error("Network error:", error);
    }
}

async function deleteTaskFromServer(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            console.log("Deleted successfully:", result.message);
        } else {
            console.error("Failed to delete:", result.detail);
        }
    } catch (error) {
        console.error("Network error:", error);
    }
}


async function fetchAndDisplayTasks() {
    try {
        const response = await fetch('/tasks');
        const tasks = await response.json();
        const taskListDiv = document.getElementById('taskList');

        taskListDiv.innerHTML = "";

        tasks.forEach(task => {
            const taskCard = document.createElement('div');
            taskCard.style.border = "1px solid black";
            taskCard.style.padding = "10px";
            taskCard.style.margin = "10px 0";

            taskCard.innerHTML = `
                <h3>ID: ${task.id}</h3>
                <p>Readiness: ${task.readiness} | Player Impact: ${task.signals.player_impact}</p>
                <button onclick="uiDeleteTask('${task.id}')">Delete</button>
                <button onclick="uiStartFullEdit('${task.id}')">Edit Task</button>
            `;

            taskListDiv.appendChild(taskCard);
        });
    } catch (error) {
        console.error("Error fetching tasks:", error);
    }
}

async function uiDeleteTask(taskId) {
    if (confirm(`Are you sure you want to delete ${taskId}?`)) {
        await deleteTaskFromServer(taskId);
        await fetchAndDisplayTasks();
    }
}

async function uiStartFullEdit(taskId) {
    try {
        const response = await fetch('/tasks');
        const tasks = await response.json();
        const taskToEdit = tasks.find(t => t.id === taskId);

        if (!taskToEdit) {
            alert("Task not found!");
            return;
        }
        document.getElementById('taskId').value = taskToEdit.id;
        document.getElementById('taskReadiness').value = taskToEdit.readiness;
        document.getElementById('playerImpact').value = taskToEdit.signals.player_impact;
        document.getElementById('taskId').disabled = true;

        currentEditTaskId = taskId;
        currentEditTaskData = taskToEdit;

        document.querySelector('#addTaskForm button[type="submit"]').innerText = "Update Task (Mettre à jour)";
        document.querySelector('h1').innerText = "Edit Task";
        window.scrollTo({ top: 0, behavior: 'smooth' });

    } catch (error) {
        console.error("Error loading task for edit:", error);
    }
}

fetchAndDisplayTasks();