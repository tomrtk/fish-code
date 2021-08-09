/*
 * jsTree
 */

import "jstree";

function attach_jstree(selector) {
  return $(selector)
    .jstree({
      core: {
        data: function (node, cb) {
          calculatedUrl =
            node.id === "#"
              ? `/projects/storage`
              : `/projects/storage/${btoa(node.id)}`;

          // Do the call
          $.ajax({
            type: "GET",
            url: calculatedUrl,
            dataType: "json",
          })
            .done(function (data) {
              cb.call(this, data);
            })
            .fail(function (data) {
              tree = $.jstree.reference(selector);

              if (data.status == 403) {
                tree.disable_node(node);
                tree.set_icon(node, "bi bi-x-circle");
                cb.call(this, "[]");
              }
            });
        },
      },
      check_callback: true,
      plugins: ["checkbox", "conditionalselect", "state", "types"],
      checkbox: {
        cascade: "down+undetermined",
        three_state: false,
      },
      conditionalselect: function (node, _) {
        return $.jstree.reference(selector).is_leaf(node);
      },
      state: {
        key: "file-browser",
        preserve_loaded: true,
        ttl: 300000,
      },
      types: {
        default: {
          icon: ["bi-file-earmark"],
        },
        folder: {
          icon: ["bi-folder"],
        },
      },
    })
    .on("ready.jstree", function (_, data) {
      $.each(data.instance.get_node("#").children, function () {
        data.instance.open_node(this);
      });
    })
    .on("select_node.jstree deselect_node.jstree", function (_, data) {
      let selected_videos = [];
      $.each(data.instance.get_selected(true), function () {
        if ($.jstree.reference(selector).is_leaf(this)) {
          selected_videos.push(this.id);
        }
      });
      selected_videos.length > 0
        ? $("#tree_data").val(JSON.stringify(selected_videos))
        : $("#tree_data").removeAttr("value");
    });
}

export { attach_jstree };
