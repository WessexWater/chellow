from net.sf.chellow.monad import Hiber
from net.sf.chellow.physical import ReadType

inv.getResponse().setContentType("text/plain")
pw = inv.getResponse().getWriter()

pw.println("Site Ids, Site Names, Supply Id, Source, MPAN core, Import / Export, DNO Name, Agreed Supply Capacity (kVA), Line Loss Factor, Line Loss Factor Description, Voltage Level, Last Read")
NON_ESTIMATE_READ_TYPES = [ReadType.NORMAL, ReadType.CUSTOMER]
for mpan in Hiber.session().createQuery("from Mpan mpan where mpan.supplyGeneration.finishDate.date is null order by mpan.mpanCore.supply.id, mpan.id").list():
    site_codes = ''
    site_names = ''
    supply_generation = mpan.getSupplyGeneration()
    supply = supply_generation.getSupply()
    mpan_top = mpan.getMpanTop()
    line_loss_factor = mpan_top.getLlf()
    if line_loss_factor.getIsImport().getBoolean():
        imp_exp = "import"
    else:
        imp_exp = "export"
    mpan_core = mpan.getMpanCore()
    for site_supply_generation in supply_generation.getSiteSupplyGenerations():
        site = site_supply_generation.getSite();
        site_codes = site_codes + site.getCode().toString() + ', '
        site_names = site_names + site.getName() + ', '
    site_codes = site_codes[:-2]
    site_names = site_names[:-2]
    #How do we find last read?
    i = 0
    found = False
    reads = Hiber.session().createQuery("from RegisterRead read where read.mpan = :mpan and read.presentType in (:readTypes) order by read.presentDate.date").setEntity('mpan', mpan).setParameterList('readTypes', NON_ESTIMATE_READ_TYPES).list()
    while found is not True and i < len(reads):
        read = reads[i]
        associated_reads = Hiber.session().createQuery("from RegisterRead read where read.invoice = :invoice and read.presentDate.date = :presentDate").setEntity('invoice', read.getInvoice()).setTimestamp('presentDate', read.getPresentDate().getDate()).list()
        found = True
        for associated_read in associated_reads:
            if read.presentType not in NON_ESTIMATE_READ_TYPES:
                found = False
                break
        i = i + 1
    last_read_date = 'None'
    if found:
        last_read_date = read.getPresentDate().toString()
    pw.println('"' + site_codes + '","' + site_names + '",' + str(supply.getId()) + "," + supply.getSource().getCode().toString() + "," + mpan_core.toString() + "," + imp_exp + "," + mpan_core.getDso().getName() + "," + str(mpan.getAgreedSupplyCapacity()) + "," + line_loss_factor.getCode().toString() + "," + line_loss_factor.getDescription() + "," + line_loss_factor.getVoltageLevel().getCode().toString() + "," + last_read_date)
    pw.flush()
pw.close()