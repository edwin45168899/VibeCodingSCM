import unittest
from copy import deepcopy
from pathlib import Path

import app as scm_app


class SCMAppTestCase(unittest.TestCase):
    def setUp(self):
        self.original_data = {
            'SUPPLIERS': deepcopy(scm_app.SUPPLIERS),
            'LOGISTICS': deepcopy(scm_app.LOGISTICS),
            'INVENTORY': deepcopy(scm_app.INVENTORY),
            'DELIVERY': deepcopy(scm_app.DELIVERY),
        }
        scm_app.SUPPLIERS = [
            {'id': 1, 'name': '供應商一', 'contact': '甲', 'phone': '1', 'address': '地址一', 'products': '商品一'},
            {'id': 2, 'name': '供應商二', 'contact': '乙', 'phone': '2', 'address': '地址二', 'products': '商品二'},
        ]
        scm_app.LOGISTICS = [
            {'id': 1, 'order_id': 'L001', 'supplier_id': 1, 'destination': '倉庫', 'status': '待出貨', 'created_at': 'now'}
        ]
        scm_app.INVENTORY = [
            {'id': 1, 'name': '商品一', 'quantity': 10, 'min_threshold': 2, 'supplier_id': 1}
        ]
        scm_app.DELIVERY = [
            {'id': 1, 'order_id': 'D001', 'customer': '客戶', 'address': '地址', 'status': '準備中', 'created_at': 'now'}
        ]
        scm_app.app.config['TESTING'] = True
        self.client = scm_app.app.test_client()

    def tearDown(self):
        for name, data in self.original_data.items():
            setattr(scm_app, name, data)


    def test_deleted_supplier_id_is_not_reused(self):
        scm_app.SUPPLIERS.pop(0)

        response = self.client.post('/suppliers/add', data={
            'name': '新供應商', 'contact': '丙', 'phone': '3', 'address': '地址三', 'products': '商品三'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual([supplier['id'] for supplier in scm_app.SUPPLIERS], [2, 3])

    def test_supplier_delete_requires_post(self):
        response = self.client.get('/suppliers/delete/1')

        self.assertEqual(response.status_code, 405)
        self.assertEqual(len(scm_app.SUPPLIERS), 2)

    def test_supplier_can_be_deleted_with_post(self):
        response = self.client.post('/suppliers/delete/1')

        self.assertEqual(response.status_code, 302)
        self.assertEqual([supplier['id'] for supplier in scm_app.SUPPLIERS], [2])

    def test_inventory_rejects_non_positive_quantity(self):
        response = self.client.post('/inventory/out/1', data={'quantity': '0'}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(scm_app.INVENTORY[0]['quantity'], 10)
        self.assertIn('數量必須是正整數', response.get_data(as_text=True))

    def test_inventory_rejects_non_numeric_quantity(self):
        response = self.client.post('/inventory/in/1', data={'quantity': 'abc'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(scm_app.INVENTORY[0]['quantity'], 10)

    def test_logistics_rejects_unknown_status(self):
        response = self.client.post('/logistics/update_status/1', data={'status': 'invalid'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(scm_app.LOGISTICS[0]['status'], '待出貨')

    def test_logistics_rejects_unknown_supplier(self):
        response = self.client.post('/logistics/add', data={
            'order_id': 'L002', 'supplier_id': '999', 'destination': '倉庫'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(scm_app.LOGISTICS), 1)

    def test_logistics_status_uses_primary_badge_when_in_transit(self):
        scm_app.LOGISTICS[0]['status'] = '運輸中'

        response = self.client.get('/logistics')
        page = response.get_data(as_text=True)

        self.assertIn('運輸中', page)
        self.assertIn('bg-primary', page)

    def test_logistics_form_uses_documented_status(self):
        page = Path(scm_app.__file__).parent.joinpath('templates', 'logistics.html').read_text(encoding='utf-8')

        self.assertIn('value="運輸中"', page)
        self.assertIn('bg-primary', page)


if __name__ == '__main__':
    unittest.main()
