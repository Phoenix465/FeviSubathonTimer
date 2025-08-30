var status_el = document.getElementById("status");
var timer_el = document.getElementById("timer");
var points_el = document.getElementById("points");

let twitch_multiplier = 1;
let youtube_multiplier = 1;

// Functions
function addContribution(contribution_id, custom_quantity = null) {
    let quantity = 1;

    if (contribution_id === "twitch_t1" || contribution_id === "twitch_t2" || contribution_id === "twitch_t3") {
        quantity = parseInt(document.querySelector('input[name="twitch-radio"]:checked').value);
    }
    if (contribution_id === "youtube_member_t1" || contribution_id === "youtube_member_t2" || contribution_id === "youtube_member_t3") {
        quantity = parseInt(document.querySelector('input[name="youtube-radio"]:checked').value);
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

document.querySelectorAll('input[name="twitch-radio"]').forEach(input => {
    input.addEventListener("change", (event) => {
        let multiplier = parseInt(event.target.value);
        console.log("Twitch Multiplier updated to ×" + multiplier);

        document.querySelectorAll('span.twitch-quantity-text').forEach(input => {
            twitch_multiplier = multiplier;

            if (multiplier === 1) {
                input.textContent = ``;
            } else {
                let padding = multiplier < 10 ? "‎ " : "";
                input.textContent = `[×${multiplier}${padding}]`;
            }
        })
    });
});

document.querySelectorAll('input[name="youtube-radio"]').forEach(input => {
    input.addEventListener("change", (event) => {
        let multiplier = parseInt(event.target.value);
        console.log("Youtube Multiplier updated to ×" + multiplier);

        document.querySelectorAll('span.youtube-quantity-text').forEach(input => {
            twitch_multiplier = multiplier;

            if (multiplier === 1) {
                input.textContent = ``;
            } else {
                let padding = multiplier < 10 ? "‎ " : "";
                input.textContent = `[×${multiplier}${padding}]`;
            }
        })
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

setInterval(function () {
    socket.emit('poll_subathon_info')
}, 100) // Poll every 100ms
