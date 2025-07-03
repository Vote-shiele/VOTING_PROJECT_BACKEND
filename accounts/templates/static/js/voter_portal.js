// Real-time vote count updates
function updateVoteCounts() {
    fetch(`/api/poll-stats/?poll_id={{ poll.id }}`)
        .then(response => response.json())
        .then(data => {
            // Update total voters
            document.getElementById('voter-count').textContent = data.total_voters;

            // Update per-candidate counts
            data.candidates.forEach(c => {
                const elem = document.getElementById(`votes-${c.id}`);
                if (elem) elem.textContent = `${c.votes} votes`;
            });
        });
}

// Countdown timer
function updateTimer() {
    const endDate = new Date("{{ poll.end_date|date:'c' }}");
    const now = new Date();
    const diff = endDate - now;

    if (diff <= 0) {
        document.getElementById('countdown-timer').textContent = "Voting ended";
        return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    document.getElementById('countdown-timer').textContent = `${days}d ${hours}h`;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Voting buttons
    document.querySelectorAll('.vote-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            fetch('/api/submit-vote/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    candidate_id: btn.dataset.candidateId,
                    poll_id: "{{ poll.id }}"
                })
            }).then(updateVoteCounts);
        });
    });

    // Refresh every 30 seconds
    setInterval(updateVoteCounts, 30000);
    setInterval(updateTimer, 60000);
    updateTimer();
});