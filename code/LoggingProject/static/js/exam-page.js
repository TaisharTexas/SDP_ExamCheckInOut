document.addEventListener("DOMContentLoaded", function () {
    // Load Flatpickr if needed
    if (typeof flatpickr === "undefined") return;

    const startPicker = flatpickr("#exam_start", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        minDate: "today",
        onChange: function(selectedDates, dateStr, instance) {
            if (!selectedDates.length) return;

            const startDate = selectedDates[0];
            const endLimit = new Date(startDate.getTime() + 24 * 60 * 60 * 1000);

            endPicker.set("minDate", startDate);
            endPicker.set("maxDate", endLimit);
        } 
    });

    const endPicker = flatpickr("#exam_end", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        minDate: "today"
    });
});
