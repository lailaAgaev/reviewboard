from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from djblets.siteconfig.models import SiteConfiguration

from reviewboard import initialize
from reviewboard.notifications.email import get_email_address_for_user, \
                                            get_email_addresses_for_group
from reviewboard.reviews.models import Group, Review, ReviewRequest


class EmailTestHelper(object):
    def assertValidRecipients(self, user_list, group_list):
        recipient_list = mail.outbox[0].to + mail.outbox[0].cc
        self.assertEqual(len(recipient_list), len(user_list) + len(group_list))

        for user in user_list:
            self.assert_(get_email_address_for_user(
                User.objects.get(username=user)) in recipient_list,
                u"user %s was not found in the recipient list" % user)

        groups = Group.objects.filter(name__in=group_list, local_site=None)
        for group in groups:
            for address in get_email_addresses_for_group(group):
                self.assert_(address in recipient_list,
                    u"group %s was not found in the recipient list" % address)


class EmailTests(TestCase, EmailTestHelper):
    """Tests the e-mail support."""
    fixtures = ['test_users', 'test_reviewrequests', 'test_scmtools',
                'test_site']

    def setUp(self):
        initialize()
        siteconfig = SiteConfiguration.objects.get_current()
        siteconfig.set("mail_send_review_mail", True)
        siteconfig.save()
        mail.outbox = []

    def testNewReviewRequestEmail(self):
        """Testing sending an e-mail when creating a new review request"""
        review_request = ReviewRequest.objects.get(
            summary="Made e-mail improvements")
        review_request.publish(review_request.submitter)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         "Review Request: Made e-mail improvements")
        self.assertValidRecipients(["grumpy", "doc"], [])

    def testReviewEmail(self):
        """Testing sending an e-mail when replying to a review request"""
        review_request = ReviewRequest.objects.get(
            summary="Add permission checking for JSON API")
        review_request.publish(review_request.submitter)

        # Clear the outbox.
        mail.outbox = []

        review = Review.objects.get(review_request=review_request,
                                    user__username="doc",
                                    base_reply_to__isnull=True)
        self.assertEqual(review.body_top, "Test")
        review.publish()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         "Re: Review Request: Add permission checking " +
                         "for JSON API")
        self.assertValidRecipients(["admin", "doc", "dopey", "grumpy"], [])

    def testReviewReplyEmail(self):
        """Testing sending an e-mail when replying to a review"""
        review_request = ReviewRequest.objects.get(
            summary="Add permission checking for JSON API")
        review_request.publish(review_request.submitter)

        base_review = Review.objects.get(review_request=review_request,
                                         user__username="doc",
                                         base_reply_to__isnull=True)
        base_review.publish()

        # Clear the outbox.
        mail.outbox = []

        reply = Review.objects.get(base_reply_to=base_review,
                                   user__username="dopey")
        reply.publish()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         "Re: Review Request: Add permission checking " +
                         "for JSON API")
        self.assertValidRecipients(["admin", "doc", "dopey", "admin"], [])

    def testUpdateReviewRequestEmail(self):
        """Testing sending an e-mail when updating a review request"""
        review_request = ReviewRequest.objects.get(
            summary="Update for cleaned_data changes")
        review_request.email_message_id = "junk"
        review_request.publish(review_request.submitter)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         "Re: Review Request: Update for cleaned_data changes")
        self.assertValidRecipients(["dopey", "doc"], ["devgroup"])


