/*
 * jsTree
 */

import "jstree";

function attach_jstree(selector) {
  return $(selector)
    .jstree({
      core: {
        data: {
          url: function (node) {
            return node.id === "#"
              ? `/projects/storage`
              : `/projects/storage/${btoa(node.id)}`;
          },
        },
      },
      plugins: ["checkbox", "conditionalselect", "state", "types"],
      checkbox: {
        cascade: "down+undetermined",
        three_state: false,
      },
      conditionalselect: function (node, _) {
        return $.jstree.reference("#jstree").is_leaf(node);
      },
      state: {
        key: "file-browser",
        preserve_loaded: true,
        ttl: 300000,
      },
      types: {
        "#": {
          valid_children: ["root"],
        },
        root: {
          valid_children: ["default"],
        },
        default: {
          valid_children: ["default", "file"],
        },
        file: {
          valid_children: [],
        },
      },
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
