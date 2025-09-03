var status_el = document.getElementById("status");
var timer_el = document.getElementById("timer");
var points_el = document.getElementById("points");

let twitch_multiplier = 1;
let youtube_multiplier = 1;
let isLoading = false;

const loadingIndicator = document.getElementById("loadingIndicator");
const historyListEl = document.getElementById("history-list");

// Functions
function addContribution(contribution_id, custom_quantity = null) {
    let quantity = 1;

    if (contribution_id === "twitch_t1" || contribution_id === "twitch_t2" || contribution_id === "twitch_t3") {
        quantity = parseInt(document.querySelector('input[name="quantity-radio"]:checked').value);
    }
    if (contribution_id === "youtube_member_t1" || contribution_id === "youtube_member_t2" || contribution_id === "youtube_member_t3") {
        quantity = parseInt(document.querySelector('input[name="quantity-radio"]:checked').value);
    }

    if (custom_quantity !== null && !isNaN(custom_quantity)) {
        quantity = custom_quantity;
    }

    console.log("Adding contribution: " + contribution_id + " x" + quantity);
    socket.emit('apply_contribution', {contribution_id: contribution_id, quantity: quantity});
}

function toggleTimer() {
    console.log("Toggling timer");
    socket.emit('toggle_timer');
}

function showContribution(title, contribution, quantity, seconds_added, points_added, theme_type) {
    showNotification(`
        <!-- Header -->
        <div class="toast-header bg-${theme_type}-subtle text-${theme_type}-dark fw-semibold">
            <strong class="me-auto fs-7">${title}</strong>
            <button type="button" class="btn-close ms-2 fs-7" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
            
        <!-- Body -->
        <div class="toast-body bg-${theme_type} text-white fw-medium fs-6_5">
            <div>
                <span class="fw-semibold">${contribution}</span> × <span class="text-muted">${quantity}</span>
            </div>
            <div class="text-end">
                <div><small>${seconds_added} sec</small></div>
                <div><small>${points_added} pts</small></div>
            </div>
        </div>
        <div class="toast-progress"></div>

    `);
}

function showError(title, message, theme_type) {
    showNotification(`
        <!-- Header -->
        <div class="toast-header bg-${theme_type}-subtle text-${theme_type}-dark fw-semibold">
            <strong class="me-auto fs-7">${title}</strong>
            <button type="button" class="btn-close ms-2 fs-7" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
            
        <!-- Body -->
        <div class="toast-body bg-${theme_type} text-white fw-medium fs-6_5">
            <div>
                ${message}
            </div>
        </div>
        <div class="toast-progress"></div>
    `);
}


function showNotification(innerHTML) {
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = "toast shadow-lg border-0rounded-3 mb-3 overflow-hidden";
    toastEl.style.maxWidth = "calc(25vw - 2rem)"
    toastEl.style.width = "calc(25vw - 2rem)"
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");

    toastEl.innerHTML = innerHTML

    // Append toast to container
    document.getElementById("toast-container").appendChild(toastEl);

    // Show toast
    const toast = new bootstrap.Toast(toastEl, {delay: 3000});
    // const toast = new bootstrap.Toast(toastEl, {delay: 50000});
    toast.show();
}

function showHistoryEvent(data, prepend = true) {
    showHistory(
        data.id,
        data.date_day,
        data.date_time,
        data.contribution_id,
        data.contribution_type,
        data.quantity,
        data.seconds_added,
        data.points_added,
        data.seconds_total,
        data.points_total_post,
        prepend
    )
}

function showHistory(id, date_day, date_time, contribution_id, contribution_type, quantity, seconds_added, points_added, seconds_total_post, points_total_post, prepend = true) {
    // Create toast element
    const historyEl = document.createElement('div');
    historyEl.className = `history-entry contribution ${contribution_type}`;
    historyEl.setAttribute("data-id", id);
    historyEl.innerHTML = `
        <!-- ID column -->
        <span class="entry-id">${id}</span>

        <!-- Vertical separator -->
        <div class="separator"></div>

        <!-- Main content -->
        <div class="entry-content flex-grow-1">
            <!-- Top row: contribution -->
            <div class="d-flex justify-content-between">
                <span class="contribution">${contribution_id}</span>
                <span class="roboto-mono-normal">×${quantity}</span>
            </div>

            <!-- Bottom row: increment left, timer + points right -->
            <div class="d-flex justify-content-between small text-muted mt-1">
                <!-- Increment info -->
                <span class="increment">${seconds_added > 0 ? '+' : ''}${seconds_added}s · ${points_added > 0 ? '+' : ''}${points_added} pts</span>
            </div>
            <div class="d-flex justify-content-between small text-muted mt-1">
                <!-- State snapshot -->
                <span class="state"> ⏱ ${seconds_total_post} </span>
                <span class="state">🔹 <span class="">${points_total_post}</span> pts </span>
            </div>

            <div class="d-flex justify-content-between small text-muted mt-1">
                <span class="timestamp roboto-mono-normal">${date_day}</span>
                <span class="timestamp roboto-mono-normal">${date_time}</span>
            </div>
        </div>
    `

    if (prepend) {
        historyListEl.prepend(historyEl);
    } else {
        if (historyListEl.lastElementChild) {
            historyListEl.insertBefore(historyEl, historyListEl.lastElementChild);
        } else {
            historyListEl.appendChild(historyEl);
        }
    }

    historyEl.onclick = function () {
        socket.emit('request_rollback', {id: historyEl.dataset.id});
    };
}

async function loadHistory() {
    if (isLoading) return;

    isLoading = true;
    loadingIndicator.classList.remove("hidden");

    let historyEnd = -1;
    if (historyListEl.children.length > 1) {
        historyEnd = Math.min(...Array.from(historyListEl.children).slice(0, -1).map(child => parseInt(child.getAttribute("data-id"))));
    }

    if (historyEnd === 0) {
        loadingIndicator.classList.add("hidden");
        isLoading = false;
        return;
    }


    if (historyEnd === -1) {
        const history_length_res = await fetch(`/api/v1/history-length`);
        if (!history_length_res.ok) {
            loadingIndicator.classList.add("hidden");
            isLoading = false;
            showError("❌ Failed to get History Length", `Solution: Turn on Server!`, "danger");
            return;
        }

        const history_length_json = await history_length_res.json();
        historyEnd = history_length_json["total"];
    }

    if (historyEnd === 0) {
        loadingIndicator.classList.add("hidden");
        isLoading = false;
        return;
    }

    let historyStart = Math.max(historyEnd - 50 - 1, 0);
    const res = await fetch(`/api/v1/history?start=${historyStart}&end=${historyEnd - 1}`);

    if (!res.ok) {
        loadingIndicator.classList.add("hidden");
        isLoading = false;
        showError("❌ Failed to get History Chunk", `Range: [${historyStart}, ${historyEnd - 1}]`, "danger");
        return;
    }

    const data = await res.json();

    data["logs"].reverse();
    data["logs"].forEach(item => {
        showHistoryEvent(item, false)
    });

    loadingIndicator.classList.add("hidden");
    isLoading = false;
}


// ---- Event Listeners ----
document.querySelectorAll('button.custom-quantity-button').forEach(button => {
    button.addEventListener("click", () => {
        let quantity_el = button.parentElement.querySelector('input');

        if (quantity_el.value === "" || isNaN(parseFloat(quantity_el.value))) {
            return;
        }

        let quantity = parseFloat(quantity_el.value);

        addContribution(button.dataset.contributionid, quantity);
    });
})


document.querySelectorAll('input.input-integer-control').forEach(input => {
    input.addEventListener("input", () => {
        input.value = input.value.replace(/\D/g, ""); // remove non-digit characters
    });
})

document.querySelectorAll('input[name="quantity-radio"]').forEach(input => {
    input.addEventListener("change", (event) => {
        let multiplier = parseInt(event.target.value);
        console.log("Multiplier updated to ×" + multiplier);

        // document.querySelectorAll('span.twitch-quantity-text').forEach(input => {
        //     twitch_multiplier = multiplier;
        //
        //     if (multiplier === 1) {
        //         input.textContent = ``;
        //     } else {
        //         let padding = multiplier < 10 ? "‎ " : "";
        //         input.textContent = `[×${multiplier}${padding}]`;
        //     }
        // })
    });
});

historyListEl.addEventListener("scroll", () => {
    if (historyListEl.scrollTop + historyListEl.clientHeight >= historyListEl.scrollHeight - 10) {
        loadHistory().then();
    }
});

// ---- Socket ----
var socket = io();
socket.on('connect', function () {
    console.log("Connected to server")
    socket.emit('connected', {data: 'connected!'});
    socket.emit('poll_subathon_info')
});

socket.on("subathon_info", function (data) {
    let formatted_seconds_left = data.formatted_seconds_left;
    let points_total = data.points_total;
    let paused = data.paused

    status_el.textContent = paused ? "Paused" : "Running"
    timer_el.textContent = formatted_seconds_left;
    points_el.textContent = points_total;
})


socket.on("notification_contribution_event", function (data) {
    showContribution(data.title, data.contribution, data.quantity, data.seconds_added, data.points_added, data.theme_type);
})

socket.on("notification_error_event", function (data) {
    showError(data.title, data.message, data.theme_type);
})

socket.on("history_event", function (data) {
    showHistoryEvent(data);
})

socket.on("rollback_confirmation", function (data) {
    // Fill modal content dynamically
    document.getElementById("rollbackId").textContent = `#${data.rollback_id}`;
    document.getElementById("rollbackDatetime").textContent = data.datetime;

    document.getElementById("rollbackTimeNew").textContent = data.new_time;
    document.getElementById("rollbackPointsNew").textContent = data.new_points;

    document.getElementById("rollbackTimeDiff").textContent = `${data.diff_time}`

    document.getElementById("rollbackPointsDiff").textContent = `${data.diff_points}`;


    // Show modal
    const rollbackModal = new bootstrap.Modal(document.getElementById('rollbackModal'));
    rollbackModal.show();

    // Confirm rollback
    document.getElementById('confirmRollback').onclick = function () {
        // Send rollback request via socket or fetch
        console.log("Rollback confirmed!");

        socket.emit('perform_rollback', {id: data.rollback_id});
        rollbackModal.hide();
    };
})

setInterval(function () {
    socket.emit('poll_subathon_info')
}, 100) // Poll every 100ms
loadHistory().then();
