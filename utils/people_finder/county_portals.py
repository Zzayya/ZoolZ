#!/usr/bin/env python3
"""
County Portal Database
Comprehensive database of county clerk websites for public records
Focus: Ohio, Pennsylvania, West Virginia
"""

from typing import Dict, List, Optional

# Ohio Counties - All 88 counties with court and property portals
OHIO_COUNTIES = {
    "Adams": {
        "courts": "https://www.adamscountyohio.com/clerk-of-courts",
        "property": "https://www.adamscountyauditor.org/search.html",
        "notes": "Manual search required"
    },
    "Allen": {
        "courts": "https://www.allencountyohio.com/clerk",
        "property": "https://www.allencountyauditor.com/search.html",
        "notes": "Property records searchable"
    },
    "Ashland": {
        "courts": "https://ashlandcounty.org/departments/clerk-of-courts",
        "property": "https://ashlandcounty.org/departments/auditor",
        "notes": "Manual search required"
    },
    "Ashtabula": {
        "courts": "https://www.ashtabulacounty.us/department/division.php?structureid=21",
        "property": "https://www.ashtabulacounty.us/department/division.php?structureid=7",
        "notes": "Property records searchable"
    },
    "Athens": {
        "courts": "https://www.athenscountygovernment.com/clerk-of-courts",
        "property": "https://www.athenscountyauditor.org/search.html",
        "notes": "Manual search required"
    },
    "Auglaize": {
        "courts": "https://www.auglaizecounty.org/departments/clerk-of-courts",
        "property": "https://www.auglaizecounty.org/departments/auditor",
        "notes": "Manual search required"
    },
    "Belmont": {
        "courts": "https://www.belmontcountyohio.org/departments/clerk-of-courts",
        "property": "https://www.belmontcountyohio.org/departments/auditor",
        "notes": "Property records searchable"
    },
    "Brown": {
        "courts": "https://www.browncountyohio.gov/departments/clerk-of-courts",
        "property": "https://www.browncountyauditor.org/search.html",
        "notes": "Manual search required"
    },
    "Butler": {
        "courts": "https://www.butlercountyohio.org/clerkofcourt",
        "property": "https://www.bcauditor.org/search.html",
        "notes": "Well-organized, searchable"
    },
    "Carroll": {
        "courts": "https://www.carrollcountyohio.us/clerk-of-courts",
        "property": "https://www.carrollcountyohio.us/auditor",
        "notes": "Manual search required"
    },
    "Champaign": {
        "courts": "https://www.co.champaign.oh.us/clerk-of-courts",
        "property": "https://www.co.champaign.oh.us/auditor",
        "notes": "Manual search required"
    },
    "Clark": {
        "courts": "https://www.clarkcountyohio.gov/departments/clerk-of-courts",
        "property": "https://www.clarkcountyauditor.org/search.html",
        "notes": "Property records searchable"
    },
    "Clermont": {
        "courts": "https://www.clermontcountyohio.gov/clerk-of-courts",
        "property": "https://www.clermontauditor.org/search.html",
        "notes": "Well-organized, searchable"
    },
    "Clinton": {
        "courts": "https://www.clintoncountyohio.gov/departments/clerk-of-courts",
        "property": "https://www.clintoncountyohio.gov/departments/auditor",
        "notes": "Manual search required"
    },
    "Columbiana": {
        "courts": "https://www.columbianacounty.org/departments/clerk-of-courts",
        "property": "https://www.columbianacounty.org/departments/auditor",
        "notes": "Property records searchable"
    },
    "Coshocton": {
        "courts": "https://www.coshoctoncounty.net/clerk-of-courts",
        "property": "https://www.coshoctoncounty.net/auditor",
        "notes": "Manual search required"
    },
    "Crawford": {
        "courts": "https://www.crawford-co.org/departments/clerk-of-courts",
        "property": "https://www.crawford-co.org/departments/auditor",
        "notes": "Manual search required"
    },
    "Cuyahoga": {
        "courts": "https://cpdocket.cp.cuyahogacounty.us/",
        "property": "https://myplace.cuyahogacounty.us/",
        "notes": "Fully searchable online system"
    },
    "Darke": {
        "courts": "https://www.darkecountyohio.gov/departments/clerk-of-courts",
        "property": "https://www.darkecountyohio.gov/departments/auditor",
        "notes": "Manual search required"
    },
    "Defiance": {
        "courts": "https://www.defiancecountyohio.com/departments/clerk-of-courts",
        "property": "https://www.defiancecountyohio.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Delaware": {
        "courts": "https://www.co.delaware.oh.us/clerk",
        "property": "https://www.co.delaware.oh.us/auditor",
        "notes": "Well-organized, searchable"
    },
    "Erie": {
        "courts": "https://eriecounty.oh.gov/departments/clerk-of-courts",
        "property": "https://eriecounty.oh.gov/departments/auditor",
        "notes": "Property records searchable"
    },
    "Fairfield": {
        "courts": "https://www.fairfieldcountyohio.gov/clerk",
        "property": "https://www.fairfieldcountyohio.gov/auditor",
        "notes": "Well-organized, searchable"
    },
    "Fayette": {
        "courts": "https://www.fayettecountyohio.com/departments/clerk-of-courts",
        "property": "https://www.fayettecountyohio.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Franklin": {
        "courts": "https://www.fcclerk.com/",
        "property": "https://www.franklincountyauditor.com/",
        "notes": "Fully searchable online system"
    },
    "Fulton": {
        "courts": "https://www.fultoncountyoh.com/departments/clerk-of-courts",
        "property": "https://www.fultoncountyoh.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Gallia": {
        "courts": "https://www.gallianet.net/departments/clerk-of-courts",
        "property": "https://www.gallianet.net/departments/auditor",
        "notes": "Manual search required"
    },
    "Geauga": {
        "courts": "https://www.geaugacounty.us/departments/clerk-of-courts",
        "property": "https://www.geaugacounty.us/departments/auditor",
        "notes": "Property records searchable"
    },
    "Greene": {
        "courts": "https://www.co.greene.oh.us/clerk",
        "property": "https://www.co.greene.oh.us/auditor",
        "notes": "Well-organized, searchable"
    },
    "Guernsey": {
        "courts": "https://www.guernseycounty.org/departments/clerk-of-courts",
        "property": "https://www.guernseycounty.org/departments/auditor",
        "notes": "Manual search required"
    },
    "Hamilton": {
        "courts": "https://www.courtclerk.org/",
        "property": "https://www.hamiltoncountyauditor.org/",
        "notes": "Fully searchable online system"
    },
    "Hancock": {
        "courts": "https://www.co.hancock.oh.us/clerk",
        "property": "https://www.co.hancock.oh.us/auditor",
        "notes": "Property records searchable"
    },
    "Hardin": {
        "courts": "https://www.hardincounty.us/departments/clerk-of-courts",
        "property": "https://www.hardincounty.us/departments/auditor",
        "notes": "Manual search required"
    },
    "Harrison": {
        "courts": "https://www.harrisoncountyohio.org/departments/clerk-of-courts",
        "property": "https://www.harrisoncountyohio.org/departments/auditor",
        "notes": "Manual search required"
    },
    "Henry": {
        "courts": "https://www.henrycountyohio.com/departments/clerk-of-courts",
        "property": "https://www.henrycountyohio.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Highland": {
        "courts": "https://www.highlandcountyohio.com/departments/clerk-of-courts",
        "property": "https://www.highlandcountyohio.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Hocking": {
        "courts": "https://www.hockingcountyohio.gov/departments/clerk-of-courts",
        "property": "https://www.hockingcountyohio.gov/departments/auditor",
        "notes": "Manual search required"
    },
    "Holmes": {
        "courts": "https://www.holmescountyohio.gov/departments/clerk-of-courts",
        "property": "https://www.holmescountyohio.gov/departments/auditor",
        "notes": "Manual search required"
    },
    "Huron": {
        "courts": "https://www.hccommissioners.com/clerk-of-courts",
        "property": "https://www.hccommissioners.com/auditor",
        "notes": "Property records searchable"
    },
    "Jackson": {
        "courts": "https://www.jacksoncountyohio.com/departments/clerk-of-courts",
        "property": "https://www.jacksoncountyohio.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Jefferson": {
        "courts": "https://www.jeffersoncountyoh.com/departments/clerk-of-courts",
        "property": "https://www.jeffersoncountyoh.com/departments/auditor",
        "notes": "Property records searchable"
    },
    "Knox": {
        "courts": "https://www.co.knox.oh.us/clerk",
        "property": "https://www.co.knox.oh.us/auditor",
        "notes": "Manual search required"
    },
    "Lake": {
        "courts": "https://www.lakecountyohio.gov/clerk",
        "property": "https://www.lakecountyohio.gov/auditor",
        "notes": "Well-organized, searchable"
    },
    "Lawrence": {
        "courts": "https://www.lawrencecountyohio.org/departments/clerk-of-courts",
        "property": "https://www.lawrencecountyohio.org/departments/auditor",
        "notes": "Manual search required"
    },
    "Licking": {
        "courts": "https://www.lcounty.com/clerk",
        "property": "https://www.lcounty.com/auditor",
        "notes": "Well-organized, searchable"
    },
    "Logan": {
        "courts": "https://www.co.logan.oh.us/clerk",
        "property": "https://www.co.logan.oh.us/auditor",
        "notes": "Manual search required"
    },
    "Lorain": {
        "courts": "https://www.loraincounty.com/clerk",
        "property": "https://www.loraincounty.com/auditor",
        "notes": "Well-organized, searchable"
    },
    "Lucas": {
        "courts": "https://lucas.oh.gegov.com/",
        "property": "https://www.co.lucas.oh.us/index.aspx?nid=518",
        "notes": "Fully searchable online system"
    },
    "Madison": {
        "courts": "https://www.co.madison.oh.us/clerk",
        "property": "https://www.co.madison.oh.us/auditor",
        "notes": "Manual search required"
    },
    "Mahoning": {
        "courts": "https://clerk.mahoningcountyoh.gov/",
        "property": "https://www.mahoningcountyoh.gov/auditor",
        "notes": "Well-organized, searchable"
    },
    "Marion": {
        "courts": "https://www.co.marion.oh.us/clerk",
        "property": "https://www.co.marion.oh.us/auditor",
        "notes": "Manual search required"
    },
    "Medina": {
        "courts": "https://www.medinaco.org/clerk",
        "property": "https://www.medinaco.org/auditor",
        "notes": "Well-organized, searchable"
    },
    "Meigs": {
        "courts": "https://www.meigscountyohio.com/departments/clerk-of-courts",
        "property": "https://www.meigscountyohio.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Mercer": {
        "courts": "https://www.mercercountyohio.org/departments/clerk-of-courts",
        "property": "https://www.mercercountyohio.org/departments/auditor",
        "notes": "Manual search required"
    },
    "Miami": {
        "courts": "https://www.miamicountyohio.gov/clerk",
        "property": "https://www.miamicountyohio.gov/auditor",
        "notes": "Property records searchable"
    },
    "Monroe": {
        "courts": "https://www.monroecountyohio.com/departments/clerk-of-courts",
        "property": "https://www.monroecountyohio.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Montgomery": {
        "courts": "https://www.mcohio.org/government/elected_officials/clerk_of_courts/",
        "property": "https://www.mcauditor.org/",
        "notes": "Fully searchable online system"
    },
    "Morgan": {
        "courts": "https://www.morgancounty-oh.gov/departments/clerk-of-courts",
        "property": "https://www.morgancounty-oh.gov/departments/auditor",
        "notes": "Manual search required"
    },
    "Morrow": {
        "courts": "https://www.morrowcounty.info/clerk",
        "property": "https://www.morrowcounty.info/auditor",
        "notes": "Manual search required"
    },
    "Muskingum": {
        "courts": "https://www.muskingumcounty.org/clerk",
        "property": "https://www.muskingumcounty.org/auditor",
        "notes": "Property records searchable"
    },
    "Noble": {
        "courts": "https://www.noblecountyohio.com/departments/clerk-of-courts",
        "property": "https://www.noblecountyohio.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Ottawa": {
        "courts": "https://www.ottawacountyohio.gov/clerk",
        "property": "https://www.ottawacountyohio.gov/auditor",
        "notes": "Manual search required"
    },
    "Paulding": {
        "courts": "https://www.pauldingcountyohio.com/departments/clerk-of-courts",
        "property": "https://www.pauldingcountyohio.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Perry": {
        "courts": "https://www.perrycountyohio.net/departments/clerk-of-courts",
        "property": "https://www.perrycountyohio.net/departments/auditor",
        "notes": "Manual search required"
    },
    "Pickaway": {
        "courts": "https://www.pickawaycounty.org/clerk",
        "property": "https://www.pickawaycounty.org/auditor",
        "notes": "Manual search required"
    },
    "Pike": {
        "courts": "https://www.pikecountyohio.org/departments/clerk-of-courts",
        "property": "https://www.pikecountyohio.org/departments/auditor",
        "notes": "Manual search required"
    },
    "Portage": {
        "courts": "https://www.portageco.com/clerk",
        "property": "https://www.portageco.com/auditor",
        "notes": "Well-organized, searchable"
    },
    "Preble": {
        "courts": "https://www.preblecountyohio.net/clerk",
        "property": "https://www.preblecountyohio.net/auditor",
        "notes": "Manual search required"
    },
    "Putnam": {
        "courts": "https://www.putnamcountyohio.gov/departments/clerk-of-courts",
        "property": "https://www.putnamcountyohio.gov/departments/auditor",
        "notes": "Manual search required"
    },
    "Richland": {
        "courts": "https://www.richlandcountyoh.us/clerk",
        "property": "https://www.richlandcountyoh.us/auditor",
        "notes": "Property records searchable"
    },
    "Ross": {
        "courts": "https://www.rossco.org/clerk",
        "property": "https://www.rossco.org/auditor",
        "notes": "Manual search required"
    },
    "Sandusky": {
        "courts": "https://www.sanduskycounty.org/clerk",
        "property": "https://www.sanduskycounty.org/auditor",
        "notes": "Property records searchable"
    },
    "Scioto": {
        "courts": "https://www.sciotocountyohio.com/clerk",
        "property": "https://www.sciotocountyohio.com/auditor",
        "notes": "Manual search required"
    },
    "Seneca": {
        "courts": "https://www.senecacounty.com/clerk",
        "property": "https://www.senecacounty.com/auditor",
        "notes": "Manual search required"
    },
    "Shelby": {
        "courts": "https://www.co.shelby.oh.us/clerk",
        "property": "https://www.co.shelby.oh.us/auditor",
        "notes": "Manual search required"
    },
    "Stark": {
        "courts": "https://www.starkcountyohio.gov/clerk",
        "property": "https://www.starkcountyohio.gov/auditor",
        "notes": "Well-organized, searchable"
    },
    "Summit": {
        "courts": "https://clerk.summitoh.net/",
        "property": "https://www.summitoh.net/auditor",
        "notes": "Fully searchable online system"
    },
    "Trumbull": {
        "courts": "https://www.trumbullcountyohio.gov/clerk",
        "property": "https://www.trumbullcountyohio.gov/auditor",
        "notes": "Property records searchable"
    },
    "Tuscarawas": {
        "courts": "https://www.co.tuscarawas.oh.us/clerk",
        "property": "https://www.co.tuscarawas.oh.us/auditor",
        "notes": "Manual search required"
    },
    "Union": {
        "courts": "https://www.co.union.oh.us/clerk",
        "property": "https://www.co.union.oh.us/auditor",
        "notes": "Manual search required"
    },
    "Van Wert": {
        "courts": "https://www.vanwertcounty.org/clerk",
        "property": "https://www.vanwertcounty.org/auditor",
        "notes": "Manual search required"
    },
    "Vinton": {
        "courts": "https://www.vintoncounty.com/departments/clerk-of-courts",
        "property": "https://www.vintoncounty.com/departments/auditor",
        "notes": "Manual search required"
    },
    "Warren": {
        "courts": "https://www.warrencountyclerk.com/",
        "property": "https://www.wcauditor.org/",
        "notes": "Well-organized, searchable"
    },
    "Washington": {
        "courts": "https://www.washingtongov.org/clerk",
        "property": "https://www.washingtongov.org/auditor",
        "notes": "Property records searchable"
    },
    "Wayne": {
        "courts": "https://www.waynecountyohio.gov/clerk",
        "property": "https://www.waynecountyohio.gov/auditor",
        "notes": "Well-organized, searchable"
    },
    "Williams": {
        "courts": "https://www.williamscountyohio.gov/clerk",
        "property": "https://www.williamscountyohio.gov/auditor",
        "notes": "Manual search required"
    },
    "Wood": {
        "courts": "https://www.co.wood.oh.us/clerk",
        "property": "https://www.co.wood.oh.us/auditor",
        "notes": "Well-organized, searchable"
    },
    "Wyandot": {
        "courts": "https://www.wyandotcounty.on.ca/clerk",
        "property": "https://www.wyandotcounty.on.ca/auditor",
        "notes": "Manual search required"
    }
}


# Pennsylvania Counties - All 67 counties
PENNSYLVANIA_COUNTIES = {
    "Adams": {
        "courts": "https://www.adamscounty.us/Govt/Courts",
        "property": "https://www.adamscounty.us/Govt/Depts/Assessment",
        "notes": "Manual search required"
    },
    "Allegheny": {
        "courts": "https://www.alleghenycourts.us/",
        "property": "https://www.alleghenycounty.us/real-estate/index.aspx",
        "notes": "Fully searchable online system"
    },
    "Armstrong": {
        "courts": "https://www.co.armstrong.pa.us/departments/courts",
        "property": "https://www.co.armstrong.pa.us/departments/assessment",
        "notes": "Manual search required"
    },
    "Beaver": {
        "courts": "https://www.beavercountypa.gov/departments/courts",
        "property": "https://www.beavercountypa.gov/departments/assessment",
        "notes": "Property records searchable"
    },
    "Bedford": {
        "courts": "https://www.bedfordcountypa.org/departments/courts",
        "property": "https://www.bedfordcountypa.org/departments/assessment",
        "notes": "Manual search required"
    },
    "Berks": {
        "courts": "https://www.co.berks.pa.us/Dept/Courts",
        "property": "https://www.co.berks.pa.us/Dept/Assessmt",
        "notes": "Well-organized, searchable"
    },
    "Blair": {
        "courts": "https://www.blairco.org/courts",
        "property": "https://www.blairco.org/assessment",
        "notes": "Manual search required"
    },
    "Bradford": {
        "courts": "https://www.bradfordco.org/departments/courts",
        "property": "https://www.bradfordco.org/departments/assessment",
        "notes": "Manual search required"
    },
    "Bucks": {
        "courts": "https://www.buckscounty.org/government/courts",
        "property": "https://www.buckscounty.org/government/AssessmentBoard",
        "notes": "Well-organized, searchable"
    },
    "Butler": {
        "courts": "https://www.butlercountypa.gov/courts",
        "property": "https://www.butlercountypa.gov/assessment",
        "notes": "Property records searchable"
    },
    "Cambria": {
        "courts": "https://www.co.cambria.pa.us/courts",
        "property": "https://www.co.cambria.pa.us/assessment",
        "notes": "Manual search required"
    },
    "Cameron": {
        "courts": "https://www.cameroncountypa.com/courts",
        "property": "https://www.cameroncountypa.com/assessment",
        "notes": "Manual search required"
    },
    "Carbon": {
        "courts": "https://www.carboncounty.com/courts",
        "property": "https://www.carboncounty.com/assessment",
        "notes": "Manual search required"
    },
    "Centre": {
        "courts": "https://www.centrecountypa.gov/courts",
        "property": "https://www.centrecountypa.gov/assessment",
        "notes": "Property records searchable"
    },
    "Chester": {
        "courts": "https://www.chesco.org/328/Courts",
        "property": "https://www.chesco.org/1366/Assessment-Office",
        "notes": "Well-organized, searchable"
    },
    "Clarion": {
        "courts": "https://www.co.clarion.pa.us/courts",
        "property": "https://www.co.clarion.pa.us/assessment",
        "notes": "Manual search required"
    },
    "Clearfield": {
        "courts": "https://www.clearfieldco.org/courts",
        "property": "https://www.clearfieldco.org/assessment",
        "notes": "Manual search required"
    },
    "Clinton": {
        "courts": "https://www.clintoncountypa.com/courts",
        "property": "https://www.clintoncountypa.com/assessment",
        "notes": "Manual search required"
    },
    "Columbia": {
        "courts": "https://www.columbiaco.org/courts",
        "property": "https://www.columbiaco.org/assessment",
        "notes": "Manual search required"
    },
    "Crawford": {
        "courts": "https://www.crawfordcountypa.net/courts",
        "property": "https://www.crawfordcountypa.net/assessment",
        "notes": "Manual search required"
    },
    "Cumberland": {
        "courts": "https://www.ccpa.net/courts",
        "property": "https://www.ccpa.net/assessment",
        "notes": "Well-organized, searchable"
    },
    "Dauphin": {
        "courts": "https://www.dauphincounty.org/government/Courts",
        "property": "https://www.dauphincounty.org/government/Departments/Assessment",
        "notes": "Well-organized, searchable"
    },
    "Delaware": {
        "courts": "https://www.delcopa.gov/courts/",
        "property": "https://www.delcopa.gov/assessment/",
        "notes": "Fully searchable online system"
    },
    "Elk": {
        "courts": "https://www.elk-county.com/courts",
        "property": "https://www.elk-county.com/assessment",
        "notes": "Manual search required"
    },
    "Erie": {
        "courts": "https://eriecountypa.gov/departments/courts/",
        "property": "https://eriecountypa.gov/departments/assessment/",
        "notes": "Well-organized, searchable"
    },
    "Fayette": {
        "courts": "https://www.fayettecountypa.org/courts",
        "property": "https://www.fayettecountypa.org/assessment",
        "notes": "Property records searchable"
    },
    "Forest": {
        "courts": "https://www.forestcounty.com/courts",
        "property": "https://www.forestcounty.com/assessment",
        "notes": "Manual search required"
    },
    "Franklin": {
        "courts": "https://www.franklincountypa.gov/courts",
        "property": "https://www.franklincountypa.gov/assessment",
        "notes": "Manual search required"
    },
    "Fulton": {
        "courts": "https://www.fultoncountypa.gov/courts",
        "property": "https://www.fultoncountypa.gov/assessment",
        "notes": "Manual search required"
    },
    "Greene": {
        "courts": "https://www.co.greene.pa.us/courts",
        "property": "https://www.co.greene.pa.us/assessment",
        "notes": "Manual search required"
    },
    "Huntingdon": {
        "courts": "https://www.huntingdoncounty.net/courts",
        "property": "https://www.huntingdoncounty.net/assessment",
        "notes": "Manual search required"
    },
    "Indiana": {
        "courts": "https://www.indianacountypa.gov/courts",
        "property": "https://www.indianacountypa.gov/assessment",
        "notes": "Manual search required"
    },
    "Jefferson": {
        "courts": "https://www.jeffersoncountypa.com/courts",
        "property": "https://www.jeffersoncountypa.com/assessment",
        "notes": "Manual search required"
    },
    "Juniata": {
        "courts": "https://www.juniataco.org/courts",
        "property": "https://www.juniataco.org/assessment",
        "notes": "Manual search required"
    },
    "Lackawanna": {
        "courts": "https://www.lackawannacounty.org/courts",
        "property": "https://www.lackawannacounty.org/assessment",
        "notes": "Property records searchable"
    },
    "Lancaster": {
        "courts": "https://co.lancaster.pa.us/courts",
        "property": "https://co.lancaster.pa.us/assessment",
        "notes": "Well-organized, searchable"
    },
    "Lawrence": {
        "courts": "https://www.lawrencecountypa.gov/courts",
        "property": "https://www.lawrencecountypa.gov/assessment",
        "notes": "Manual search required"
    },
    "Lebanon": {
        "courts": "https://www.lebcounty.org/courts",
        "property": "https://www.lebcounty.org/assessment",
        "notes": "Manual search required"
    },
    "Lehigh": {
        "courts": "https://www.lehighcounty.org/courts",
        "property": "https://www.lehighcounty.org/assessment",
        "notes": "Well-organized, searchable"
    },
    "Luzerne": {
        "courts": "https://www.luzernecounty.org/courts",
        "property": "https://www.luzernecounty.org/assessment",
        "notes": "Property records searchable"
    },
    "Lycoming": {
        "courts": "https://www.lyco.org/courts",
        "property": "https://www.lyco.org/assessment",
        "notes": "Manual search required"
    },
    "McKean": {
        "courts": "https://www.mckeancountypa.org/courts",
        "property": "https://www.mckeancountypa.org/assessment",
        "notes": "Manual search required"
    },
    "Mercer": {
        "courts": "https://www.mercercountypa.gov/courts",
        "property": "https://www.mercercountypa.gov/assessment",
        "notes": "Property records searchable"
    },
    "Mifflin": {
        "courts": "https://www.co.mifflin.pa.us/courts",
        "property": "https://www.co.mifflin.pa.us/assessment",
        "notes": "Manual search required"
    },
    "Monroe": {
        "courts": "https://www.monroecountypa.gov/courts",
        "property": "https://www.monroecountypa.gov/assessment",
        "notes": "Manual search required"
    },
    "Montgomery": {
        "courts": "https://www.montcopa.org/courts",
        "property": "https://www.montcopa.org/assessment",
        "notes": "Fully searchable online system"
    },
    "Montour": {
        "courts": "https://www.montourco.org/courts",
        "property": "https://www.montourco.org/assessment",
        "notes": "Manual search required"
    },
    "Northampton": {
        "courts": "https://www.northamptoncounty.org/COURTS",
        "property": "https://www.northamptoncounty.org/ASSESSMENT",
        "notes": "Well-organized, searchable"
    },
    "Northumberland": {
        "courts": "https://www.norrycopa.net/courts",
        "property": "https://www.norrycopa.net/assessment",
        "notes": "Manual search required"
    },
    "Perry": {
        "courts": "https://www.perryco.org/courts",
        "property": "https://www.perryco.org/assessment",
        "notes": "Manual search required"
    },
    "Philadelphia": {
        "courts": "https://www.courts.phila.gov/",
        "property": "https://property.phila.gov/",
        "notes": "Fully searchable online system"
    },
    "Pike": {
        "courts": "https://www.pikepa.org/courts",
        "property": "https://www.pikepa.org/assessment",
        "notes": "Manual search required"
    },
    "Potter": {
        "courts": "https://www.pottercountypa.net/courts",
        "property": "https://www.pottercountypa.net/assessment",
        "notes": "Manual search required"
    },
    "Schuylkill": {
        "courts": "https://www.co.schuylkill.pa.us/courts",
        "property": "https://www.co.schuylkill.pa.us/assessment",
        "notes": "Manual search required"
    },
    "Snyder": {
        "courts": "https://www.snydercounty.org/courts",
        "property": "https://www.snydercounty.org/assessment",
        "notes": "Manual search required"
    },
    "Somerset": {
        "courts": "https://www.co.somerset.pa.us/courts",
        "property": "https://www.co.somerset.pa.us/assessment",
        "notes": "Manual search required"
    },
    "Sullivan": {
        "courts": "https://www.sullivancounty-pa.us/courts",
        "property": "https://www.sullivancounty-pa.us/assessment",
        "notes": "Manual search required"
    },
    "Susquehanna": {
        "courts": "https://www.susqco.com/courts",
        "property": "https://www.susqco.com/assessment",
        "notes": "Manual search required"
    },
    "Tioga": {
        "courts": "https://www.tiogacountypa.us/courts",
        "property": "https://www.tiogacountypa.us/assessment",
        "notes": "Manual search required"
    },
    "Union": {
        "courts": "https://www.unionco.org/courts",
        "property": "https://www.unionco.org/assessment",
        "notes": "Manual search required"
    },
    "Venango": {
        "courts": "https://www.co.venango.pa.us/courts",
        "property": "https://www.co.venango.pa.us/assessment",
        "notes": "Manual search required"
    },
    "Warren": {
        "courts": "https://www.warrencountypa.gov/courts",
        "property": "https://www.warrencountypa.gov/assessment",
        "notes": "Manual search required"
    },
    "Washington": {
        "courts": "https://www.washingtoncountypa.gov/courts",
        "property": "https://www.washingtoncountypa.gov/assessment",
        "notes": "Property records searchable"
    },
    "Wayne": {
        "courts": "https://www.waynecountypa.gov/courts",
        "property": "https://www.waynecountypa.gov/assessment",
        "notes": "Manual search required"
    },
    "Westmoreland": {
        "courts": "https://www.co.westmoreland.pa.us/courts",
        "property": "https://www.co.westmoreland.pa.us/assessment",
        "notes": "Well-organized, searchable"
    },
    "Wyoming": {
        "courts": "https://www.wycopa.org/courts",
        "property": "https://www.wycopa.org/assessment",
        "notes": "Manual search required"
    },
    "York": {
        "courts": "https://www.yorkcountypa.gov/courts",
        "property": "https://www.yorkcountypa.gov/assessment",
        "notes": "Well-organized, searchable"
    }
}


# West Virginia Counties - All 55 counties
WEST_VIRGINIA_COUNTIES = {
    "Barbour": {
        "courts": "https://barbourcountywv.com/county-clerk",
        "property": "https://barbourcountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Berkeley": {
        "courts": "https://www.berkeleycountywv.org/county-clerk",
        "property": "https://www.berkeleycountywv.org/assessor",
        "notes": "Property records searchable"
    },
    "Boone": {
        "courts": "https://boonecountywv.org/county-clerk",
        "property": "https://boonecountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Braxton": {
        "courts": "https://www.braxtoncountywv.org/county-clerk",
        "property": "https://www.braxtoncountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Brooke": {
        "courts": "https://www.brookecountywv.org/county-clerk",
        "property": "https://www.brookecountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Cabell": {
        "courts": "https://www.cabellcounty.org/county-clerk",
        "property": "https://www.cabellcounty.org/assessor",
        "notes": "Well-organized, searchable"
    },
    "Calhoun": {
        "courts": "https://calhouncountywv.org/county-clerk",
        "property": "https://calhouncountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Clay": {
        "courts": "https://www.claycountywv.com/county-clerk",
        "property": "https://www.claycountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Doddridge": {
        "courts": "https://doddridgecounty.com/county-clerk",
        "property": "https://doddridgecounty.com/assessor",
        "notes": "Manual search required"
    },
    "Fayette": {
        "courts": "https://fayettecountywv.com/county-clerk",
        "property": "https://fayettecountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Gilmer": {
        "courts": "https://gilmercounty.org/county-clerk",
        "property": "https://gilmercounty.org/assessor",
        "notes": "Manual search required"
    },
    "Grant": {
        "courts": "https://grantcountywv.com/county-clerk",
        "property": "https://grantcountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Greenbrier": {
        "courts": "https://www.greenbriercountywv.com/county-clerk",
        "property": "https://www.greenbriercountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Hampshire": {
        "courts": "https://hampshirewv.com/county-clerk",
        "property": "https://hampshirewv.com/assessor",
        "notes": "Manual search required"
    },
    "Hancock": {
        "courts": "https://www.hancockcountywv.org/county-clerk",
        "property": "https://www.hancockcountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Hardy": {
        "courts": "https://hardycountywv.com/county-clerk",
        "property": "https://hardycountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Harrison": {
        "courts": "https://www.harrisoncountywv.com/county-clerk",
        "property": "https://www.harrisoncountywv.com/assessor",
        "notes": "Property records searchable"
    },
    "Jackson": {
        "courts": "https://www.jacksoncountywv.com/county-clerk",
        "property": "https://www.jacksoncountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Jefferson": {
        "courts": "https://www.jeffersoncountywv.org/county-clerk",
        "property": "https://www.jeffersoncountywv.org/assessor",
        "notes": "Well-organized, searchable"
    },
    "Kanawha": {
        "courts": "https://www.kanawha.us/pages/CountyClerk.aspx",
        "property": "https://www.kanawha.us/pages/Assessor.aspx",
        "notes": "Well-organized, searchable"
    },
    "Lewis": {
        "courts": "https://www.lewiscountywv.gov/county-clerk",
        "property": "https://www.lewiscountywv.gov/assessor",
        "notes": "Manual search required"
    },
    "Lincoln": {
        "courts": "https://lincolncountywv.org/county-clerk",
        "property": "https://lincolncountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Logan": {
        "courts": "https://www.logancountywv.com/county-clerk",
        "property": "https://www.logancountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Marion": {
        "courts": "https://marioncountywv.com/county-clerk",
        "property": "https://marioncountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Marshall": {
        "courts": "https://www.marshallcountywv.org/county-clerk",
        "property": "https://www.marshallcountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Mason": {
        "courts": "https://masoncountywv.org/county-clerk",
        "property": "https://masoncountywv.org/assessor",
        "notes": "Manual search required"
    },
    "McDowell": {
        "courts": "https://www.mcdowellcountywv.com/county-clerk",
        "property": "https://www.mcdowellcountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Mercer": {
        "courts": "https://www.mercercountywv.org/county-clerk",
        "property": "https://www.mercercountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Mineral": {
        "courts": "https://mineralcountywv.com/county-clerk",
        "property": "https://mineralcountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Mingo": {
        "courts": "https://mingocountywv.com/county-clerk",
        "property": "https://mingocountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Monongalia": {
        "courts": "https://www.monongaliacounty.com/county-clerk",
        "property": "https://www.monongaliacounty.com/assessor",
        "notes": "Well-organized, searchable"
    },
    "Monroe": {
        "courts": "https://monroecountywv.com/county-clerk",
        "property": "https://monroecountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Morgan": {
        "courts": "https://morgancountywv.gov/county-clerk",
        "property": "https://morgancountywv.gov/assessor",
        "notes": "Manual search required"
    },
    "Nicholas": {
        "courts": "https://nicholascountywv.org/county-clerk",
        "property": "https://nicholascountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Ohio": {
        "courts": "https://www.ohiocountywv.com/county-clerk",
        "property": "https://www.ohiocountywv.com/assessor",
        "notes": "Property records searchable"
    },
    "Pendleton": {
        "courts": "https://pendletoncountywv.com/county-clerk",
        "property": "https://pendletoncountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Pleasants": {
        "courts": "https://pleasantscountywv.org/county-clerk",
        "property": "https://pleasantscountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Pocahontas": {
        "courts": "https://pocahontascountywv.com/county-clerk",
        "property": "https://pocahontascountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Preston": {
        "courts": "https://www.prestoncountywv.gov/county-clerk",
        "property": "https://www.prestoncountywv.gov/assessor",
        "notes": "Manual search required"
    },
    "Putnam": {
        "courts": "https://putnamcountywv.org/county-clerk",
        "property": "https://putnamcountywv.org/assessor",
        "notes": "Well-organized, searchable"
    },
    "Raleigh": {
        "courts": "https://raleighcountywv.com/county-clerk",
        "property": "https://raleighcountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Randolph": {
        "courts": "https://randolphcountywv.com/county-clerk",
        "property": "https://randolphcountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Ritchie": {
        "courts": "https://ritchiecountywv.com/county-clerk",
        "property": "https://ritchiecountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Roane": {
        "courts": "https://roanecountywv.com/county-clerk",
        "property": "https://roanecountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Summers": {
        "courts": "https://summerscountywv.org/county-clerk",
        "property": "https://summerscountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Taylor": {
        "courts": "https://taylorcountywv.com/county-clerk",
        "property": "https://taylorcountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Tucker": {
        "courts": "https://tuckercountywv.org/county-clerk",
        "property": "https://tuckercountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Tyler": {
        "courts": "https://www.tylercountywv.com/county-clerk",
        "property": "https://www.tylercountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Upshur": {
        "courts": "https://upshurcountywv.gov/county-clerk",
        "property": "https://upshurcountywv.gov/assessor",
        "notes": "Manual search required"
    },
    "Wayne": {
        "courts": "https://waynecountywv.org/county-clerk",
        "property": "https://waynecountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Webster": {
        "courts": "https://webstercountywv.org/county-clerk",
        "property": "https://webstercountywv.org/assessor",
        "notes": "Manual search required"
    },
    "Wetzel": {
        "courts": "https://wetzelcountywv.com/county-clerk",
        "property": "https://wetzelcountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Wirt": {
        "courts": "https://wirtcountywv.com/county-clerk",
        "property": "https://wirtcountywv.com/assessor",
        "notes": "Manual search required"
    },
    "Wood": {
        "courts": "https://www.woodcountywv.com/county-clerk",
        "property": "https://www.woodcountywv.com/assessor",
        "notes": "Well-organized, searchable"
    },
    "Wyoming": {
        "courts": "https://wyomingcountywv.com/county-clerk",
        "property": "https://wyomingcountywv.com/assessor",
        "notes": "Manual search required"
    }
}


def get_county_portal(state: str, county: str, record_type: str = "courts") -> Optional[Dict]:
    """
    Get portal URL and info for a specific county

    Args:
        state: Two-letter state code (OH, PA, WV)
        county: County name
        record_type: "courts" or "property"

    Returns:
        Dict with portal info or None if not found
    """
    state = state.upper()
    county = county.title()

    county_data = None
    if state == "OH":
        county_data = OHIO_COUNTIES.get(county)
    elif state == "PA":
        county_data = PENNSYLVANIA_COUNTIES.get(county)
    elif state == "WV":
        county_data = WEST_VIRGINIA_COUNTIES.get(county)

    if not county_data:
        return None

    return {
        "state": state,
        "county": county,
        "url": county_data.get(record_type, ""),
        "notes": county_data.get("notes", ""),
        "record_type": record_type
    }


def get_all_counties_for_state(state: str) -> List[str]:
    """Get list of all county names for a given state"""
    state = state.upper()
    if state == "OH":
        return list(OHIO_COUNTIES.keys())
    elif state == "PA":
        return list(PENNSYLVANIA_COUNTIES.keys())
    elif state == "WV":
        return list(WEST_VIRGINIA_COUNTIES.keys())
    return []


def get_county_count() -> Dict[str, int]:
    """Get total county counts"""
    return {
        "OH": len(OHIO_COUNTIES),
        "PA": len(PENNSYLVANIA_COUNTIES),
        "WV": len(WEST_VIRGINIA_COUNTIES),
        "total": len(OHIO_COUNTIES) + len(PENNSYLVANIA_COUNTIES) + len(WEST_VIRGINIA_COUNTIES)
    }
