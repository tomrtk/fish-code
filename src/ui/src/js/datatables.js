/*
 * datatables.js  *
 *
 * Holdes the code for DataTables.
 *
 */

import DataTable from "datatables.net-dt";

const createIframeMarkup = function (objectId) {
  return `
  <div id="preview-dialog-bg">
    <div id="preview-dialog">
      <button type="button"><i class="bi bi-x-lg"></i></button>
      <iframe
        src="/projects/objects/${objectId}/preview"
        class="w-full aspect-video"
      ></iframe>
    </div>
  </div>
  `;
};

const createPreviewLinkIcon = function (objectId) {
  return `
    <a
      id="preview-${objectId}"
      class="btn-object-preview"
      href="/projects/objects/${objectId}/preview"
      target="_blank"
      ><i class="bi bi-film"></i>
    </a>`;
};

// Create table
let table = new DataTable("#object_list", {
  order: [[1, "asc"]],
  ordering: false,
  pageLength: 25,
  processing: false,
  searching: false,
  serverSide: true,

  ajax: {
    url: window.location.href + "/objects",
    type: "POST",
    dataSrc: "data",
  },

  columns: [
    {
      data: "enumarate",
      render: function (_1, _2, _3, meta) {
        return meta.row + meta.settings._iDisplayStart + 1;
      },
    },
    { data: "id", visible: false },
    { data: "label" },
    { data: "time_in" },
    { data: "time_out" },
    {
      data: "probability",
      render: function (data, _2, _3) {
        const color = data >= 0.5 ? "black" : "red";
        const val = DataTable.render.number("", ".", 2, "").display(data);

        return '<span style="color:' + color + '">' + val + "</span>";
      },
    },
    { data: "video_ids" },
    {
      data: "preview",
      render: function (_1, _2, row, _4) {
        return createPreviewLinkIcon(row.id);
      },
    },
  ],
});

/*
 * Preview Dialog
 */

table.on("preDraw", function () {
  table.rows().every(function () {
    var row = $(this.node());
    var obj = table.row(this).data();

    // remove link in cell
    var cell = row.find("td:eq(6)").find("a");
    cell[0].removeAttribute("href");
    cell[0].removeAttribute("target");

    // Create iframe on click
    cell
      .bind("click", function () {
        $("body").prepend(createIframeMarkup(obj.id));
        $("body").addClass("overflow-hidden");
        $(document).on("click", "#preview-dialog-bg", function () {
          $(this).remove();
          $("body").removeClass("overflow-hidden");
        });
        $(document).on("click", "#preview-dialog-bg button", function () {
          $(this).remove();
          $("body").removeClass("overflow-hidden");
        });
      })
      .css("cursor", "pointer");
  });
});

export default table;
