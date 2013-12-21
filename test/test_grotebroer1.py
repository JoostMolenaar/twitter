import time
import unittest
import re

import mock

import twitter
import bot.grotebroer1

class TestGroteBroer1_UserStream(unittest.TestCase):
    def setUp(self):
        self.api = mock.Mock()
        self.userstream = mock.Mock()
        self.aivd = bot.grotebroer1.UserStream('grotebroer1', api=self.api, userstream=self.userstream)

    def test_start(self):
        with mock.patch('threading.Thread', autospec=True) as thread_class:
            self.aivd.start()
            thread_class.assert_called_with(name='GroteBroer1-UserStream', target=self.aivd.run)
            self.assertTrue(thread_class.return_value.start.called)

    def test_stop(self):
        self.aivd.stop()
        self.assertFalse(self.aivd.running)

    def test_aborts_run(self):
        self.api.config = { 
            u'terms': [u'test'],
            u'admins': ['j0057m'] }

        self.userstream.get_user.return_value = [
            { u'direct_message': { u'id': u'1',
                                   u'text': u'+verdacht',
                                   u'sender_screen_name': u'j0057m',
                                   u'sender': { u'screen_name': u'j0057m' } } } ]
        
        self.aivd.run()

        self.assertFalse(self.api.save.called)

    def test_dm_answer_query(self):
        self.api.config = { 
            u'terms': [u'test'],
            u'admins': ['j0057m'] }

        self.userstream.get_user.return_value = [
            { 'something_else': {} },
            '',
            { 'direct_message': { u'id': u'1',
                                  u'text': u'?',
                                  u'sender_screen_name': u'j0057m',
                                  u'sender': { u'screen_name': u'j0057m' } } },
            { 'direct_message': { u'id': u'2',
                                  u'text': u'who am i?',
                                  u'sender_screen_name': u'not_an_admin',
                                  u'sender': { u'screen_name': u'not_an_admin' } } } ]

        self.aivd.running = True
        self.aivd.run()

        self.api.post_direct_messages_new.assert_called_with(
            screen_name=u'j0057m',
            text=u'test')
        self.api.post_direct_messages_destroy.assert_called_with(id=u'1')

    def test_dm_add_term(self):
        self.api.config = { 
            u'terms': [u'test'],
            u'admins': ['j0057m'] }

        self.userstream.get_user.return_value = [
            { u'direct_message': { u'id': u'1',
                                   u'text': u'+verdacht',
                                   u'sender_screen_name': u'j0057m',
                                   u'sender': { u'screen_name': u'j0057m' } } } ]

        self.aivd.running = True
        self.aivd.run()

        self.api.post_direct_messages_new.assert_called_with(
            screen_name=u'j0057m',
            text=u'Term added: verdacht')
        self.api.post_direct_messages_destroy.assert_called_with(id=u'1')

        self.assertTrue(self.api.save.called)

        self.assertEqual([u'test', u'verdacht'], self.api.config[u'terms'])

    def test_dm_add_existing_term(self):
        self.api.config = { 
            u'terms': [u'test'],
            u'admins': ['j0057m'] }

        self.userstream.get_user.return_value = [
            { u'direct_message': { u'id': u'1',
                                   u'text': u'+test',
                                   u'sender_screen_name': u'j0057m',
                                   u'sender': { u'screen_name': u'j0057m' } } } ]

        self.aivd.running = True
        self.aivd.run()

        self.api.post_direct_messages_new.assert_called_with(
            screen_name=u'j0057m',
            text=u'Term already in list: test')
        self.api.post_direct_messages_destroy.assert_called_with(id=u'1')

        self.assertFalse(self.api.save.called)

        self.assertEqual([u'test'], self.api.config[u'terms'])

    def test_dm_del_term(self):
        self.api.config = { 
            u'terms': [u'test'],
            u'admins': ['j0057m'] }

        self.userstream.get_user.return_value = [
            { u'direct_message': { u'id': u'1',
                                   u'text': u'-test',
                                   u'sender_screen_name': u'j0057m',
                                   u'sender': { u'screen_name': u'j0057m' } } } ]

        self.aivd.running = True
        self.aivd.run()

        self.api.post_direct_messages_new.assert_called_with(
            screen_name=u'j0057m',
            text=u'Term removed: test')
        self.api.post_direct_messages_destroy.assert_called_with(id=u'1')

        self.assertEqual([], self.api.config[u'terms'])

    def test_dm_del_term_nonexisting(self):
        self.api.config = { 
            u'terms': [u'test'],
            u'admins': ['j0057m'] }

        self.userstream.get_user.return_value = [
            { u'direct_message': { u'id': u'1',
                                   u'text': u'-verdacht',
                                   u'sender_screen_name': u'j0057m',
                                   u'sender': { u'screen_name': u'j0057m' } } } ]

        self.aivd.running = True
        self.aivd.run()

        self.api.post_direct_messages_new.assert_called_with(
            screen_name=u'j0057m',
            text=u'Term not in list: verdacht')
        self.api.post_direct_messages_destroy.assert_called_with(id=u'1')

        self.assertEqual([u'test'], self.api.config[u'terms'])

    def test_dm_send_help(self):
        self.api.config = { 
            u'terms': [u'test'],
            u'admins': ['j0057m'] }

        self.userstream.get_user.return_value = [
            { u'direct_message': { u'id': u'1',
                                   u'text': u'spam',
                                   u'sender_screen_name': u'j0057m',
                                   u'sender': { u'screen_name': u'j0057m' } } } ]

        self.aivd.running = True
        self.aivd.run()

        self.api.post_direct_messages_new.assert_called_with(
            screen_name=u'j0057m',
            text=u'Usage: +term | -term | ?')
        self.api.post_direct_messages_destroy.assert_called_with(id=u'1')

    def test_dm_set_chance(self):
        self.api.config = { 
            u'terms': [u'test'],
            u'admins': ['j0057m'],
            u'chance': 13 }

        self.userstream.get_user.return_value = [
            { u'direct_message': { u'id': u'1',
                                   u'text': u'42%',
                                   u'sender_screen_name': u'j0057m',
                                   u'sender': { u'screen_name': u'j0057m' } } } ]

        self.aivd.running = True
        self.aivd.run()

        self.api.post_direct_messages_new.assert_called_with(
            screen_name=u'j0057m',
            text=u'Retweet/follow chance is now 42%')
        self.api.post_direct_messages_destroy.assert_called_with(id=u'1')

        self.assertEqual(self.api.config[u'chance'], 42)

class TestGroteBroer1_Firehose(unittest.TestCase):
    def setUp(self):
        self.api = mock.Mock()
        self.stream = mock.Mock()
        self.aivd = bot.grotebroer1.Firehose('grotebroer1', api=self.api, stream=self.stream)

    def test_start(self):
        with mock.patch('threading.Thread', autospec=True) as thread_class:
            self.aivd.start()
            thread_class.assert_called_with(name='GroteBroer1-Firehose', target=self.aivd.run)
            self.assertTrue(thread_class.return_value.start.called)

    def test_stop(self):
        self.aivd.stop()
        self.assertFalse(self.aivd.running)

    def test_aborts_run(self):
        self.api.config = { u'chance': 100 }

        self.stream.get_statuses_filter = lambda *a, **k: [
            '',
            { u'text': u'test',
              u'id': u'1',
              u'user': { 'screen_name': 'test1' } } ]

        self.aivd.run()
        
        self.assertFalse(self.api.post_statuses_retweet.called)

    def test_skip_no_update(self):
        self.api.config = { u'chance': 100 }

        self.stream.get_statuses_filter = lambda *a, **k: [
            '',
            { u'text': u'test',
              u'id': u'1',
              u'user': { 'screen_name': 'test1' } } ]

        self.aivd.running = True
        self.aivd.run()
        
        self.assertFalse(self.api.post_statuses_retweet.called)

    def test_match(self):
        self.api.config = { u'chance': 100 }

        self.stream.get_statuses_filter = lambda *a, **k: [
            '',
            { u'text': u'test',
              u'id': u'1',
              u'user': { 'screen_name': 'test1' } } ]

        self.aivd.term_regex = r'\b(?:test)\b'
        self.aivd.terms = re.compile(self.aivd.term_regex)

        self.aivd.running = True
        self.aivd.run()

        self.api.post_statuses_retweet.assert_called_with(u'1')
        self.api.post_friendships_create.assert_called_with(screen_name=u'test1')

    def test_no_match(self):
        self.api.config = { u'chance': 100 }

        self.stream.get_statuses_filter = lambda *a, **k: [
            { u'text': u'dit is niet interessant',
              u'id': u'1',
              u'user': { 'screen_name': 'test1' } } ]

        self.aivd.term_regex = r'\b(?:test)\b'
        self.aivd.terms = re.compile(self.aivd.term_regex)

        self.aivd.running = True
        self.aivd.run()

        self.assertFalse(self.api.post_statuses_retweet.called)
        self.assertFalse(self.api.post_friendships_create.called)

    def test_bad_luck(self):
        self.api.config = { u'chance': 0 }

        self.stream.get_statuses_filter = lambda *a, **k: [
            '',
            { u'text': u'test',
              u'id': u'1',
              u'user': { 'screen_name': 'test1' } } ]

        self.aivd.term_regex = r'\b(?:test)\b'
        self.aivd.terms = re.compile(self.aivd.term_regex)

        self.aivd.running = True
        self.aivd.run()

        self.assertFalse(self.api.post_statuses_retweet.called)
        self.assertFalse(self.api.post_friendships_create.called)

    def test_update_regex(self):
        self.api.config = { u'terms': [u'a', u'b'] }

        self.aivd.update(None)
        self.aivd.update(None)

        self.assertEqual(self.aivd.term_regex, r'\b(?:a|b)\b')

