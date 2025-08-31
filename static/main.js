var status_el = document.getElementById("status");
var timer_el = document.getElementById("timer");
var points_el = document.getElementById("points");

let twitch_multiplier = 1;
let youtube_multiplier = 1;

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
    toastEl.className = "toast col-4 shadow-lg border-0rounded-3 mb-3 overflow-hidden";
    toastEl.style.maxWidth = "200px"
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




setInterval(function () {
    socket.emit('poll_subathon_info')
}, 100) // Poll every 100ms
