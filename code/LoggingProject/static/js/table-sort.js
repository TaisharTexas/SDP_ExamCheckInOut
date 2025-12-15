let sortDirectionMap = {};

function sortTableByColumn(tableId, columnIndex) {
  const table = document.getElementById(tableId);
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);

  // Initialize direction if not set yet
  if (!(tableId in sortDirectionMap)) {
    sortDirectionMap[tableId] = {};
  }
  if (!(columnIndex in sortDirectionMap[tableId])) {
    sortDirectionMap[tableId][columnIndex] = true; // ascending
  }

  const direction = sortDirectionMap[tableId][columnIndex];

  rows.sort((a, b) => {
    const aText = a.cells[columnIndex].innerText.trim().toLowerCase();
    const bText = b.cells[columnIndex].innerText.trim().toLowerCase();
    return direction ? aText.localeCompare(bText) : bText.localeCompare(aText);
  });

  rows.forEach((row) => tbody.appendChild(row));

  // Toggle for next time
  sortDirectionMap[tableId][columnIndex] = !direction;

  //Update arrow icon
  const headers = table.querySelectorAll("th");
  headers.forEach((th, index) => {
    const svg = th.querySelector(".sort-icon");
    if (svg) {
      const asc = svg.querySelector(".asc-icon");
      const desc = svg.querySelector(".desc-icon");

      if (index === columnIndex) {
        if (direction) {
          asc.classList.remove("hidden");
          desc.classList.add("hidden");
        } else {
          asc.classList.add("hidden");
          desc.classList.remove("hidden");
        }
      } else {
        asc.classList.remove("hidden");
        desc.classList.add("hidden");
      }
    }
  });
}
