import logging
import re

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import ugettext as _
from djblets.util.misc import get_object_or_none

from reviewboard.diffviewer import forms as diffviewer_forms
from reviewboard.diffviewer.models import DiffSet
from reviewboard.filemanager.models import UploadedFile
from reviewboard.reviews.errors import OwnershipError
from reviewboard.reviews.models import DefaultReviewer, ReviewRequest, \
                                       ReviewRequestDraft, UploadedFileComment
from reviewboard.scmtools.errors import SCMError, ChangeNumberInUseError, \
                                        InvalidChangeNumberError, \
                                        ChangeSetError
from reviewboard.scmtools.models import Repository
from reviewboard.site.models import LocalSite


class UploadFileForm(forms.Form):
    """ A form that handles uploading of new files.

    A file takes a path argument and optionally a caption.
    """
    caption = forms.CharField(required=False)
    path = forms.FileField(required=True)

    def create(self, file, review_request):
        upFile = UploadedFile(caption=self.cleaned_data['caption'],
                              draft_caption=self.cleaned_data['caption'])
        upFile.upfile.save(file.name, file, save=True)

        review_request.files.add(upFile)

        draft = ReviewRequestDraft.create(review_request)
        draft.files.add(upFile)
        draft.save()

        return upFile
