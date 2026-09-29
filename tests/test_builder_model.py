import unittest

from mangomod.builder_model import Action, BuilderDraft, Trigger
from mangomod.config_parser import BindingEntry, parse_config_text


class BuilderModelTests(unittest.TestCase):
    def test_unconfirmed_attributes_keep_arguments_editable(self):
        action = Action.create('viewprev_have_client')
        self.assertEqual(action.raw_args, '')
        entry = BindingEntry(command='viewprev_have_client', args='1,future')
        self.assertEqual(Action.from_binding(entry).arguments(), '1,future')

    def test_shared_keyboard_conflict_marks_existing_and_new_bindings(self):
        doc = parse_config_text('bind=SUPER,Return,spawn,foot\n')
        draft = BuilderDraft(actions=[Action.create('togglefloating')])

        proposed = draft.proposed_document(doc, allow_conflicts=True)

        self.assertEqual(
            proposed.serialize(),
            'bindc=SUPER,Return,spawn,foot\n'
            'bindc=SUPER,Return,togglefloating\n',
        )

    def test_multiple_actions_share_one_keyboard_trigger(self):
        doc = parse_config_text('')
        draft = BuilderDraft(actions=[Action.create('togglefloating'), Action.create('centerwin')])

        self.assertEqual(
            proposed := draft.proposed_document(doc).serialize(),
            'bindc=SUPER,Return,togglefloating\n'
            'bindc=SUPER,Return,centerwin\n',
        )
        self.assertIn('bindc=', proposed)

    def test_keymode_insert_restores_previous_mode(self):
        doc = parse_config_text('keymode=resize\nbind=NONE,h,resizewin,-10,0\n')
        resize = Action.create('resizewin')
        resize.values.update({'w': '+10', 'h': '0'})
        draft = BuilderDraft(
            trigger=Trigger(modifiers='NONE', key='l', keymode='default'),
            actions=[resize],
        )

        self.assertEqual(
            draft.proposed_document(doc).serialize(),
            'keymode=resize\n'
            'bind=NONE,h,resizewin,-10,0\n'
            'keymode=default\n'
            'bind=NONE,l,resizewin,+10,0\n'
            'keymode=resize\n',
        )

    def test_editing_existing_binding_preserves_type_and_inline_comment(self):
        doc = parse_config_text('bindl=SUPER,Return,spawn,foot # old terminal\n')
        source = doc.entries[0]
        draft = BuilderDraft.from_binding(source)
        draft.actions[0].values['command'] = 'kitty'

        self.assertEqual(
            draft.proposed_document(doc).serialize(),
            'bindl=SUPER,Return,spawn,kitty # old terminal\n',
        )

    def test_unknown_command_raw_arguments_round_trip(self):
        doc = parse_config_text('bind=SUPER,M,future_cmd,one,two,three\n')
        draft = BuilderDraft.from_binding(doc.entries[0])

        self.assertEqual(draft.actions[0].raw_args, 'one,two,three')
        self.assertEqual(draft.proposed_document(doc).serialize(), doc.serialize())

    def test_common_keymode_conflicts_with_every_mode(self):
        doc = parse_config_text('keymode=common\nbind=SUPER,Return,spawn,foot\n')
        draft = BuilderDraft(actions=[Action.create('togglefloating')])

        self.assertEqual(len(draft.conflicts([doc])), 1)

    def test_release_flag_does_not_conflict_with_press_binding(self):
        doc = parse_config_text('bindr=SUPER,Return,spawn,foot\n')
        draft = BuilderDraft(actions=[Action.create('togglefloating')])

        self.assertEqual(draft.conflicts([doc]), [])

    def test_non_keyboard_trigger_is_not_marked_shareable(self):
        doc = parse_config_text('mousebind=SUPER,btn_left,moveresize,curmove\n')
        draft = BuilderDraft(
            trigger=Trigger(kind='mouse', modifiers='SUPER', key='btn_left'),
            actions=[Action.create('togglefloating')],
        )

        self.assertEqual(len(draft.conflicts([doc])), 1)
        proposed = draft.proposed_document(doc, allow_conflicts=True)
        self.assertTrue(isinstance(proposed.entries[0], BindingEntry) is False)
        self.assertIn('mousebind=SUPER,btn_left,togglefloating\n', proposed.serialize())


if __name__ == '__main__':
    unittest.main()
