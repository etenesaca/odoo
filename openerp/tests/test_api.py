
from openerp.tools import mute_logger
from openerp.osv.orm import Record, Recordset, Null
import common


class TestAPI(common.TransactionCase):
    """ test the new API of the ORM """

    def setUp(self):
        super(TestAPI, self).setUp()
        self.Partner = self.registry('res.partner')
        self.Users = self.registry('res.users')

    @mute_logger('openerp.osv.orm')
    def test_00_query(self):
        """ Build a recordset, and check its contents. """
        domain = [('name', 'ilike', 'j')]
        ids = self.Partner.search(self.cr, self.uid, domain)
        partners = self.Partner.query(self.cr, self.uid, domain)

        # partners is a collection of browse records corresponding to ids
        self.assertTrue(ids)
        self.assertTrue(partners)
        for p in partners:
            self.assertIsInstance(p, Record)
        self.assertEqual([p.id for p in partners], ids)

    @mute_logger('openerp.osv.orm')
    def test_01_query_offset(self):
        """ Build a recordset with offset, and check equivalence. """
        ids = self.Partner.search(self.cr, self.uid, [], offset=10)
        partners = self.Partner.browse(self.cr, self.uid, ids)
        self.assertTrue(partners)

        partners1 = self.Partner.query(self.cr, self.uid, [], offset=10)
        self.assertEqual(list(partners1), list(partners))

        partners2 = self.Partner.query(self.cr, self.uid, [])[10:]
        self.assertEqual(list(partners2), list(partners))

    @mute_logger('openerp.osv.orm')
    def test_02_query_limit(self):
        """ Build a recordset with offset, and check equivalence. """
        ids = self.Partner.search(self.cr, self.uid, [], limit=10)
        partners = self.Partner.browse(self.cr, self.uid, ids)
        self.assertTrue(partners)

        partners1 = self.Partner.query(self.cr, self.uid, [], limit=10)
        self.assertEqual(list(partners1), list(partners))

        partners2 = self.Partner.query(self.cr, self.uid, [])[:10]
        self.assertEqual(list(partners2), list(partners))

    @mute_logger('openerp.osv.orm')
    def test_03_query_offset_limit(self):
        """ Build a recordset with offset and limit, and check equivalence. """
        ids = self.Partner.search(self.cr, self.uid, [], offset=3, limit=7)
        partners = self.Partner.browse(self.cr, self.uid, ids)
        self.assertTrue(partners)

        partners1 = self.Partner.query(self.cr, self.uid, [], offset=3, limit=7)
        self.assertEqual(list(partners1), list(partners))

        partners2 = self.Partner.query(self.cr, self.uid, [])[3:10]
        self.assertEqual(list(partners2), list(partners))

    @mute_logger('openerp.osv.orm')
    def test_04_query_multi_slicing(self):
        """ Build a recordset with multiple slicings, and check equivalence. """
        ids = self.Partner.search(self.cr, self.uid, [], offset=3, limit=7)
        partners = self.Partner.browse(self.cr, self.uid, ids)
        self.assertTrue(partners)

        partners1 = self.Partner.query(self.cr, self.uid, [])[1:10][2:12]
        self.assertEqual(list(partners1), list(partners))

    @mute_logger('openerp.osv.orm')
    def test_05_immutable(self):
        """ Check that a recordset remains the same, even after updates. """
        domain = [('name', 'ilike', 'j')]
        partners = self.Partner.query(self.cr, self.uid, domain)
        self.assertTrue(partners)
        ids = map(int, partners)

        # modify those partners, and check that partners has not changed
        self.Partner.write(self.cr, self.uid, ids, {'active': False})
        self.assertEqual(ids, map(int, partners))

        # redo the query, and check that the result is now empty
        partners2 = self.Partner.query(self.cr, self.uid, domain)
        self.assertFalse(partners2)

    @mute_logger('openerp.osv.orm')
    def test_06_fields(self):
        """ Check that relation fields return records, recordsets or nulls. """
        user = self.Users.browse(self.cr, self.uid, self.uid)
        self.assertIsInstance(user, Record)
        # Check for a programming bug: accessing 'partner_id' should read all
        # prefetched fields in the record cache, and many2many fields should not
        # be prefetched.  When rewriting the record access, I observed that
        # many2many fields may be anyway read, and put in the cache as a list of
        # ids instead of a recordset.
        self.assertIsInstance(user.partner_id, Record)
        self.assertIsInstance(user.groups_id, Recordset)

        partners = self.Partner.query(self.cr, self.uid, [])
        for name, cinfo in partners._all_columns.iteritems():
            if cinfo.column._type in ('many2one', 'reference'):
                for p in partners:
                    if p[name]:
                        self.assertIsInstance(p[name], Record)
                    else:
                        self.assertIsInstance(p[name], Null)
            elif cinfo.column._type in ('one2many', 'many2many'):
                for p in partners:
                    self.assertIsInstance(p[name], Recordset)

    @mute_logger('openerp.osv.orm')
    def test_07_null(self):
        """ Check behavior of nulls. """
        # select a partner without a parent
        partner = self.Partner.query(self.cr, self.uid, [('parent_id', '=', False)])[0]

        # check partner
        self.assertTrue(partner)
        self.assertIsInstance(partner, Record)
        self.assertEqual(partner._name, 'res.partner')

        # check partner.parent_id
        self.assertFalse(partner.parent_id)
        self.assertIsInstance(partner.parent_id, Null)
        self.assertEqual(partner.parent_id._name, 'res.partner')

        # check partner.parent_id.id
        self.assertFalse(partner.parent_id.id)
        self.assertIs(partner.parent_id.id, False)

        # check partner.parent_id.user_id
        self.assertFalse(partner.parent_id.user_id)
        self.assertIsInstance(partner.parent_id.user_id, Null)
        self.assertEqual(partner.parent_id.user_id._name, 'res.users')

        # check partner.parent_id.user_id.name
        self.assertFalse(partner.parent_id.user_id.name)
        self.assertIs(partner.parent_id.user_id.name, False)

        # check partner.parent_id.user_id.name.groups_id
        self.assertFalse(partner.parent_id.user_id.groups_id)
        self.assertIsInstance(partner.parent_id.user_id.groups_id, Recordset)
        self.assertEqual(partner.parent_id.user_id.groups_id._name, 'res.groups')

    @mute_logger('openerp.osv.orm')
    def test_10_old_old(self):
        """ Call old-style methods in the old-fashioned way. """
        domain = [('name', 'ilike', 'j')]
        partners = self.Partner.query(self.cr, self.uid, domain)
        self.assertTrue(partners)
        ids = map(int, partners)

        # call method write on partners itself, and check its effect
        partners.write(self.cr, self.uid, ids, {'active': False})
        for p in partners:
            self.assertFalse(p.active)

    @mute_logger('openerp.osv.orm')
    def test_20_old_new(self):
        """ Call old-style methods in the new API style. """
        domain = [('name', 'ilike', 'j')]
        partners = self.Partner.query(self.cr, self.uid, domain)
        self.assertTrue(partners)

        # call method write on partners itself, and check its effect
        partners.write({'active': False})
        for p in partners:
            self.assertFalse(p.active)

    @mute_logger('openerp.osv.orm')
    def test_25_old_new(self):
        """ Call old-style methods on records (new API style). """
        domain = [('name', 'ilike', 'j')]
        partners = self.Partner.query(self.cr, self.uid, domain)
        self.assertTrue(partners)

        # call method write on partner records
        for p in partners:
            p.write({'active': False})

        # re-browse the records to check the method's effect
        for p in partners.browse(map(int, partners)):
            self.assertFalse(p.active)

    @mute_logger('openerp.osv.orm')
    def test_30_new_old(self):
        """ Call new-style methods in the old-fashioned way. """
        domain = [('name', 'ilike', 'j')]
        partners = self.Partner.query(self.cr, self.uid, domain)
        self.assertTrue(partners)
        ids = map(int, partners)

        # call method name_get on partners itself, and check its effect
        res = partners.name_get(self.cr, self.uid, ids)
        self.assertEqual(len(res), len(ids))
        self.assertEqual(set(val[0] for val in res), set(ids))

    @mute_logger('openerp.osv.orm')
    def test_40_new_new(self):
        """ Call new-style methods in the new API style. """
        domain = [('name', 'ilike', 'j')]
        partners = self.Partner.query(self.cr, self.uid, domain)
        self.assertTrue(partners)

        # call method name_get on partners itself, and check its effect
        res = partners.name_get()
        self.assertEqual(len(res), len(partners))
        self.assertEqual(set(val[0] for val in res), set(map(int, partners)))

    @mute_logger('openerp.osv.orm')
    def test_45_new_new(self):
        """ Call new-style methods on records (new API style). """
        domain = [('name', 'ilike', 'j')]
        partners = self.Partner.query(self.cr, self.uid, domain)
        self.assertTrue(partners)

        # call method name_get on partner records, and check its effect
        for p in partners:
            res = p.name_get()
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0][0], p.id)

    @mute_logger('openerp.osv.orm')
    def test_50_session(self):
        """ Call session methods. """
        domain = [('name', 'ilike', 'j')]
        partners1 = self.Partner.query(self.cr, self.uid, domain).recordset
        self.assertTrue(partners1)

        # check content of partners1.session
        self.assertEqual(partners1.session.cr, self.cr)
        self.assertEqual(partners1.session.uid, self.uid)
        self.assertEqual(partners1.session.user.id, self.uid)
        self.assertFalse(partners1.session.context)

        # access another model from partners1.session
        Users = partners1.session.model('res.users')
        self.assertEqual(Users.session, partners1.session)

        # pick another user
        user1 = partners1.session.user
        user2 = Users.query([('id', '!=', user1.id)])[0]
        self.assertTrue(user2.is_record())
        self.assertNotEqual(user1, user2)

        # copy recordset with another user
        partners2 = partners1.with_session(user=user2, lang=user2.lang or 'en_US')
        self.assertEqual(partners2.session.user, user2)
        self.assertNotEqual(partners2.session, partners1.session)
        self.assertTrue(partners2.is_recordset())
        self.assertEqual(partners2, partners1)

    @mute_logger('openerp.osv.orm')
    def test_50_record_recordset(self):
        """ Check properties record and recordset. """
        ps = self.Partner.query(self.cr, self.uid, [('name', 'ilike', 'a')], limit=1)
        self.assertEqual(ps.recordset, ps)
        p = ps.record
        self.assertEqual(p, ps[0])
        self.assertEqual(p.recordset, ps)

    @mute_logger('openerp.osv.orm')
    def test_60_contains(self):
        """ Test membership on recordset. """
        ps = self.Partner.query(self.cr, self.uid, [('name', 'ilike', 'a')], limit=1)
        p = ps.record
        ps = self.Partner.query(self.cr, self.uid, [('name', 'ilike', 'a')])
        self.assertTrue(p in ps)

    @mute_logger('openerp.osv.orm')
    def test_60_and(self):
        """ Check conjunction of recordsets. """
        pa = self.Partner.query(self.cr, self.uid, [('name', 'ilike', 'a')])
        pb = self.Partner.query(self.cr, self.uid, [('name', 'ilike', 'b')])
        pab = pa & pb
        self.assertEqual(set(pab), set(pa) & set(pb))

    @mute_logger('openerp.osv.orm')
    def test_60_or(self):
        """ Check union of recordsets. """
        pa = self.Partner.query(self.cr, self.uid, [('name', 'ilike', 'a')])
        pb = self.Partner.query(self.cr, self.uid, [('name', 'ilike', 'b')])
        pab = pa | pb
        self.assertEqual(set(pab), set(pa) | set(pb))

    @mute_logger('openerp.osv.orm')
    def test_60_sub(self):
        """ Check difference of recordsets. """
        pa = self.Partner.query(self.cr, self.uid, [('name', 'ilike', 'a')])
        pb = self.Partner.query(self.cr, self.uid, [('name', 'ilike', 'ag')])
        pab = pa - pb
        self.assertEqual(set(pab), set(pa) - set(pb))
