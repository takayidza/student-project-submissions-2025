$(document).ready(function () {
    $("table").DataTable({
        responsive: true,
        paging: true,
        searching: true,
        ordering: true,
        info: true,
        lengthMenu: [10, 25, 50, 100],
        columnDefs: [
            { orderable: false, targets: -1 } // Disables sorting on the last column (usually actions)
        ]
    });
});