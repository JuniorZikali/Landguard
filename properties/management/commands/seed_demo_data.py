"""
Seed the database with realistic Zimbabwe test data for demonstration.

Usage:
    python manage.py seed_demo_data

This creates:
  - 4 user accounts (one per role): registrar, sellers (incl. a 'land baron'), buyer
  - ~12 properties across Harare suburbs
  - Several transactions including fraud scenarios:
      * a clean low-risk listing
      * a seller-mismatch (impersonation) listing
      * a double-listing (two sellers, same property)
      * a price-anomaly listing
      * a land-baron with many recent listings
"""
from datetime import date, timedelta
from decimal import Decimal
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from properties.models import Property
from transactions.models import Transaction
from transactions.risk_engine import apply_evaluation


HARARE_SUBURBS = [
    ('Borrowdale', 17.7444, 31.0833),
    ('Avondale', -17.7833, 31.0333),
    ('Mount Pleasant', -17.7700, 31.0500),
    ('Highlands', -17.7833, 31.0833),
    ('Glen Lorne', -17.7333, 31.1167),
    ('Greendale', -17.8167, 31.1333),
    ('Marlborough', -17.7500, 30.9833),
    ('Hatfield', -17.8500, 31.0833),
    ('Belgravia', -17.8000, 31.0333),
    ('Eastlea', -17.8333, 31.0833),
    ('Newlands', -17.7833, 31.0833),
    ('Mabvuku', -17.8167, 31.1833),
]


class Command(BaseCommand):
    help = "Seed demo data for the LandGuard prototype."
    
    def handle(self, *args, **options):
        self.stdout.write("Seeding LandGuard demo data...")
        
        # Wipe existing data (except superusers)
        Transaction.objects.all().delete()
        Property.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
        # Create users
        registrar = self._create_user(
            'registrar1', 'registrar@landguard.zw', 'TestPass123!',
            'Tendai Moyo', '63-1111111A11', 'registrar',
            phone='+263 77 111 1111',
        )
        registrar.profile.is_verified = True
        registrar.profile.save()
        
        seller1 = self._create_user(
            'seller_chamu', 'chamu@example.com', 'TestPass123!',
            'Chamunorwa Ndlovu', '63-2222222B22', 'seller',
            phone='+263 77 222 2222',
        )
        seller1.profile.is_verified = True
        seller1.profile.save()
        
        seller2 = self._create_user(
            'seller_rumbi', 'rumbi@example.com', 'TestPass123!',
            'Rumbidzai Chikafu', '63-3333333C33', 'seller',
            phone='+263 77 333 3333',
        )
        seller2.profile.is_verified = True
        seller2.profile.save()
        
        # The "land baron" — unverified, will list many properties
        land_baron = self._create_user(
            'baron_x', 'baron@example.com', 'TestPass123!',
            'Tatenda Mukamuri', '63-9999999X99', 'seller',
            phone='+263 77 999 9999',
        )
        # Note: not marked is_verified — adds an unverified_owner flag.
        
        impersonator = self._create_user(
            'fakeseller', 'impersonator@example.com', 'TestPass123!',
            'Suspicious Person', '63-4444444D44', 'seller',
            phone='+263 77 444 4444',
        )
        
        buyer = self._create_user(
            'buyer1', 'buyer@example.com', 'TestPass123!',
            'Tafadzwa Sibanda', '63-5555555E55', 'buyer',
            phone='+263 77 555 5555',
        )
        
        self.stdout.write(self.style.SUCCESS(f"  Created {User.objects.count()} users"))
        
        # Create properties
        properties = []
        owners = [seller1, seller2, registrar, land_baron]
        for i in range(12):
            suburb, lat, lng = random.choice(HARARE_SUBURBS)
            year = random.randint(2010, 2023)
            seq = random.randint(1000, 9999)
            owner = random.choice(owners)
            prop = Property.objects.create(
                title_deed_number=f"{seq}/{year}",
                stand_number=str(random.randint(100, 9999)),
                suburb=suburb,
                city='Harare',
                province='Harare',
                gps_latitude=Decimal(f"{lat:.6f}"),
                gps_longitude=Decimal(f"{lng:.6f}"),
                size_sqm=Decimal(random.choice([500, 750, 1000, 1500, 2000, 4000])),
                property_type=random.choice(['residential', 'residential', 'commercial']),
                registered_owner=owner,
                registration_date=date(year, random.randint(1, 12), random.randint(1, 28)),
                status='active',
                market_value_estimate=Decimal(random.choice([
                    45000, 60000, 85000, 120000, 180000, 250000, 350000,
                ])),
                description=f"A {random.choice(['cosy', 'spacious', 'modern'])} property in {suburb}.",
            )
            properties.append(prop)
        
        # Mark one property as disputed and one as flagged for testing
        properties[0].status = 'disputed'
        properties[0].save()
        properties[1].status = 'flagged'
        properties[1].save()
        
        self.stdout.write(self.style.SUCCESS(f"  Created {len(properties)} properties"))
        
        # Create transactions — including fraud scenarios
        
        # 1. Clean, low-risk listing
        clean_prop = properties[5]  # owned by some random seller
        Transaction.objects.create(
            related_property=clean_prop,
            seller=clean_prop.registered_owner,
            listed_price=clean_prop.market_value_estimate * Decimal('0.95'),
            status='listed',
        )
        
        # 2. Impersonation: seller is NOT the registered owner
        impersonation_prop = properties[6]
        Transaction.objects.create(
            related_property=impersonation_prop,
            seller=impersonator,  # not the registered owner!
            listed_price=impersonation_prop.market_value_estimate * Decimal('0.90'),
            status='listed',
        )
        
        # 3. Double-listing — same property listed by two sellers
        double_prop = properties[7]
        Transaction.objects.create(
            related_property=double_prop,
            seller=double_prop.registered_owner,
            listed_price=double_prop.market_value_estimate,
            status='listed',
        )
        Transaction.objects.create(
            related_property=double_prop,
            seller=impersonator,
            listed_price=double_prop.market_value_estimate * Decimal('0.85'),
            status='listed',
        )
        
        # 4. Price anomaly — listed at 30% of market value
        cheap_prop = properties[8]
        Transaction.objects.create(
            related_property=cheap_prop,
            seller=cheap_prop.registered_owner,
            listed_price=cheap_prop.market_value_estimate * Decimal('0.30'),
            status='listed',
        )
        
        # 5. Land-baron pattern — same seller lists many properties
        baron_props = [
            properties[i] for i in range(len(properties))
            if properties[i].registered_owner == land_baron
        ]
        # Make sure baron has a few — assign extra if needed
        for i in range(min(5, len(properties))):
            p = properties[-(i + 1)]
            if p.registered_owner != land_baron:
                p.registered_owner = land_baron
                p.save()
                baron_props.append(p)
        
        # Ensure we have at least 6 baron listings
        for prop in baron_props[:6]:
            Transaction.objects.create(
                related_property=prop,
                seller=land_baron,
                listed_price=prop.market_value_estimate * Decimal('0.95'),
                status='listed',
            )
        
        # Run risk evaluation on all transactions
        for txn in Transaction.objects.all():
            apply_evaluation(txn)
        
        self.stdout.write(self.style.SUCCESS(
            f"  Created {Transaction.objects.count()} transactions and evaluated fraud risk"
        ))
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write("Login credentials (all use password: TestPass123!):")
        self.stdout.write("  Registrar:  registrar@landguard.zw")
        self.stdout.write("  Seller 1:   chamu@example.com")
        self.stdout.write("  Seller 2:   rumbi@example.com")
        self.stdout.write("  Land Baron: baron@example.com")
        self.stdout.write("  Buyer:      buyer@example.com")
        self.stdout.write("")
        self.stdout.write("Try the deed checker with: 1234/2020 (or any deed in /properties/)")
        self.stdout.write("")

    def _create_user(self, username, email, password, full_name, national_id, role, phone=''):
        user = User.objects.create_user(
            username=username, email=email, password=password,
        )
        # Signal already created a Profile — update it with real values
        Profile.objects.filter(user=user).update(
            full_name=full_name,
            national_id=national_id,
            role=role,
            phone=phone,
        )
        user.refresh_from_db()
        return user