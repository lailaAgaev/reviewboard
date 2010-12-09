//State:
var gFileComments;


/*
 * Creates a comment block to the screenshot comments area.
 *
 * @param {jQuery} container  The container for the comment block.
 * @param {array}  comments   The list of comments in this block.
 *
 * @return {object} The comment block.
 */
function fileCommentBlock(container, file_id, comments) {
    var self = this;

    this.file_id = file_id;

    // location of selection link
    this.hasDraft = false;
    this.comments = [];
    this.canDelete = false;
    this.draftComment = null;

    this.el = $("a#"+this.file_id, container);
    this.tooltip = $.tooltip(this.el, {
        side: "lrbt"
    }).addClass("comments");
    this.flag = $('<div class="selection-flag"/>').appendTo(this.el);

    /*
     * Find out if there's any draft comments, and filter them out of the
     * stored list of comments.
     */
    if (comments && comments.length > 0) {
        for (var i in comments) {
            var comment = comments[i];

            if (comment.localdraft) {
                this._createDraftComment(comment.comment_id, this.file_id, comment.text);
            } else {
                this.comments.push(comment);
            }
        }
    } else {
        this._createDraftComment(null, this.file_id);
    }

    this.updateCount();
    this.updateTooltip();

    return this;
}

jQuery.extend(fileCommentBlock.prototype, {
    /*
     * Updates the tooltip contents.
     */
    updateTooltip: function() {
        function addEntry(text) {
            var item = $("<li>").appendTo(list);
            item.text(text.truncate());
            return item;
        }

        this.tooltip.empty();
        var list = $("<ul/>").appendTo(this.tooltip);

        if (this.draftComment != null) {
            addEntry(this.draftComment.text).addClass("draft");
        }

        for (comment in this.comments) {
            addEntry(this.comments[comment].text);
        }
    },

    /*
     * Updates the displayed number of comments in the comment block.
     *
     * If there's a draft comment, it will be added to the count. Otherwise,
     * this depends solely on the number of published comments.
     */
    updateCount: function() {
        var count = this.comments.length;

        if (this.draftComment != null) {
            count++;
        }

        this.count = count;
        this.flag.html(count);
    },

    /*
     * Notifies the user of some update. This notification appears in the
     * comment area.
     *
     * @param {string} text  The notification text.
     */
    notify: function(text, cb) {
        var offset = this.el.offset();

        var bubble = $("<div/>")
            .addClass("bubble")
            .appendTo(this.el)
            .text(text);

        bubble
            .css("opacity", 0)
            .move(Math.round((this.el.width()  - bubble.width())  / 2),
                  Math.round((this.el.height() - bubble.height()) / 2))
            .animate({
                top: "-=10px",
                opacity: 0.8
            }, 350, "swing")
            .delay(1200)
            .animate({
                top: "+=10px",
                opacity: 0
            }, 350, "swing", function() {
                bubble.remove();

                if ($.isFunction(cb)) {
                    cb();
                }
            });
    },

    _createDraftComment: function(id, file_id, text) {
        if (this.draftComment != null) {
            return;
        }

        var self = this;
        var el = this.el;
        var comment = gReviewRequest.createReview().createFileComment(
            id, this.file_id);

        if (text) {
            comment.text = text;
        }

        $.event.add(comment, "textChanged", function() {
            self.updateTooltip();
        });

        $.event.add(comment, "deleted", function() {
            el.queue(function() {
                self.notify("Comment Deleted", function() {
                    el.dequeue();
                });
            });
        });

        $.event.add(comment, "destroyed", function() {
            /* Discard the comment block if empty. */
            if (self.comments.length > 0) {
                el.removeClass("draft");
                self.flag.removeClass("flag-draft");
                self.updateCount();
                self.updateTooltip();
            }
        });

        $.event.add(comment, "saved", function() {
            self.updateCount();
            self.updateTooltip();
            gFileComments[comment.file_id] += 
            self.notify("Comment Saved");
            showReviewBanner();
        });

        this.draftComment = comment;
        el.addClass("draft");
        this.flag.addClass("flag-draft");
    }
});

/*
 * Creates a box for creating and seeing all comments on a file.
 *
 * @param {object} regions  The regions containing comments.
 *
 * @return {jQuery} This jQuery.
 */
jQuery.fn.fileCommentBox = function(regions) {
    var self = this;

    /* State */
    var activeCommentBlock = null;
    gFileComments = regions;

    /* Page elements */
    var file_list = this;

    var activeSelection =
        $('<div id="selection-interactive"/>')
        .prependTo(file_list)
        .hide();

    var commentDetail = $("#comment-detail")
        .commentDlg()
        .bind("close", function() { activeCommentBlock = null; })
        .css("z-index", 999);
    commentDetail.prependTo("body");

    /*
     * Register events on the selection area for handling new comment
     * creation.
     */
    $([file_list[0]])
        .mousedown(function(evt) {
            if (evt.which == 1 && !activeCommentBlock &&
                !$(evt.target).hasClass("selection-flag")) {
                var offset = file_list.offset();
                activeSelection.beginX =
                    evt.pageX - Math.floor(offset.left) - 1;
                activeSelection.beginY =
                    evt.pageY - Math.floor(offset.top) - 1;

                activeSelection
                    .move(activeSelection.beginX, activeSelection.beginY)
                    .width(1)
                    .height(1)
                    .show();

                if (activeSelection.is(":hidden")) {
                    commentDetail.hide();
                }

                return false;
            }
        })
        .mouseup(function(evt) {
            if (!activeCommentBlock && activeSelection.is(":visible")) {
                evt.stopPropagation();

                var width  = activeSelection.width();
                var height = activeSelection.height();
                var offset = activeSelection.position();

                activeSelection.hide();

                if (activeCommentBlock) {
                        showCommentDlg(addCommentBlock(file_id));
                }
            }
        })
        .mousemove(function(evt) {
            if (!activeCommentBlock && activeSelection.is(":visible")) {
                var offset = file_list.offset();
                var x = evt.pageX - Math.floor(offset.left) - 1;
                var y = evt.pageY - Math.floor(offset.top) - 1;

                activeSelection
                    .css(activeSelection.beginX <= x
                         ? {
                               left:  activeSelection.beginX,
                               width: x - activeSelection.beginX
                           }
                         : {
                               left:  x,
                               width: activeSelection.beginX - x
                           })
                    .css(activeSelection.beginY <= y
                         ? {
                               top:    activeSelection.beginY,
                               height: y - activeSelection.beginY
                           }
                         : {
                               top:    y,
                               height: activeSelection.beginY - y
                           });

                return false;
            }
        })
        .proxyTouchEvents();

    /* Add all existing comment regions to the page. */
    for (i in regions) {
        var file_id = i;
        var comments = regions[i];
        addCommentBlock(file_id,
                        comments);
    }
    /*
     * Adds a new comment block to the selection area. This may contain
     * existing comments or may be a newly created comment block.
     *
     * @param {int}   file_id   The id of the file this comment is attached to.
     * @param {array} comments  The list of comments in this block.
     *
     * @return {CommentBlock} The new comment block.
     */
    function addCommentBlock(file_id, comments) {

        //get existing comments!
        if (!comments && gFileComments){
            comments = gFileComments[file_id];
        }
        var commentBlock = new fileCommentBlock(file_list[0], file_id, comments)
        commentBlock.el.click(function() {
            showCommentDlg(commentBlock);
        });

        return commentBlock;
    }

    /*
     * Shows the comment details dialog for a comment block.
     *
     * @param {CommentBlock} commentBlock  The comment block to show.
     */
    function showCommentDlg(commentBlock) {
        commentDetail
            .one("close", function() {
                commentBlock._createDraftComment(file_id);
                activeCommentBlock = commentBlock;

                commentDetail
                    .setDraftComment(commentBlock.draftComment)
                    .setCommentsList(commentBlock.comments,
                                     "file_comment")
                    .positionToSide(commentBlock.flag, {
                        side: 'b',
                        fitOnScreen: true
                    });
                commentDetail.open();
            })
            .close()
    }

    return this;
}
// vim: set et ts=4:
