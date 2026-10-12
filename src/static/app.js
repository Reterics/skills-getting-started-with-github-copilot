document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  let messageTimer;
  let refreshVersion = 0;

  function showMessage(message, type) {
    clearTimeout(messageTimer);
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    messageTimer = setTimeout(() => messageDiv.classList.add("hidden"), 5000);
  }

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  async function unregister(activity, email, button) {
    button.disabled = true;
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Unable to unregister.");
      showMessage(result.message, "success");
      await fetchActivities();
    } catch (error) {
      showMessage(error.message || "Failed to unregister. Please try again.", "error");
    } finally {
      button.disabled = false;
    }
  }

  async function fetchActivities() {
    const version = ++refreshVersion;
    try {
      const response = await fetch("/activities");
      if (!response.ok) throw new Error("Unable to load activities.");
      const activities = await response.json();
      if (version !== refreshVersion) return;
      const selectedActivity = activitySelect.value;
      const cards = document.createDocumentFragment();
      const options = document.createDocumentFragment();
      const placeholder = element("option", "-- Select an activity --");
      placeholder.value = "";
      options.appendChild(placeholder);

      Object.entries(activities).forEach(([name, details]) => {
        const card = element("div", undefined, "activity-card");
        const spotsLeft = details.max_participants - details.participants.length;
        card.append(
          element("h4", name),
          element("p", details.description),
          element("p", `Schedule: ${details.schedule}`),
          element("p", `Availability: ${spotsLeft} spots left`)
        );
        const participants = element("div", undefined, "participants");
        participants.appendChild(element("h5", `Participants (${details.participants.length})`));
        if (details.participants.length === 0) {
          participants.appendChild(element("p", "No participants yet. Be the first to join!", "empty-participants"));
        } else {
          const list = element("ul");
          list.setAttribute("role", "list");
          details.participants.forEach((email) => {
            const item = element("li");
            const button = element("button", "×", "unregister-button");
            button.type = "button";
            button.setAttribute("aria-label", `Unregister ${email} from ${name}`);
            button.title = `Unregister ${email}`;
            button.addEventListener("click", () => unregister(name, email, button));
            item.append(element("span", email), button);
            list.appendChild(item);
          });
          participants.appendChild(list);
        }
        card.appendChild(participants);
        cards.appendChild(card);
        const option = element("option", name);
        option.value = name;
        options.appendChild(option);
      });

      activitiesList.replaceChildren(cards);
      activitySelect.replaceChildren(options);
      if (Object.hasOwn(activities, selectedActivity)) activitySelect.value = selectedActivity;
    } catch (error) {
      if (version !== refreshVersion) return;
      activitiesList.replaceChildren(element("p", "Failed to load activities. Refresh the page to try again."));
      showMessage("Could not refresh activities. Refresh the page to see the latest registrations.", "error");
      console.error("Error fetching activities:", error);
    }
  }

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = signupForm.querySelector('button[type="submit"]');
    if (submitButton.disabled) return;
    const email = document.getElementById("email").value;
    const activity = activitySelect.value;
    submitButton.disabled = true;
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        { method: "POST" }
      );
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Unable to sign up.");
      showMessage(result.message, "success");
      signupForm.reset();
      await fetchActivities();
    } catch (error) {
      showMessage(error.message || "Failed to sign up. Please try again.", "error");
    } finally {
      submitButton.disabled = false;
    }
  });

  fetchActivities();
});
