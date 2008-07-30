package net.sf.chellow.billing;

import java.util.Date;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.DsoCode;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Llfc;
import net.sf.chellow.physical.LlfcCode;
import net.sf.chellow.physical.Llfcs;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.MpanTops;
import net.sf.chellow.physical.Participant;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Dso extends Party {
	static public Provider getDso(DsoCode code) throws HttpException {
		Provider dso = findDso(code.getString());
		if (dso == null) {
			throw new UserException("There is no DSO with the code '" + code
					+ "'.");
		}
		return dso;
	}

	static public Provider findDso(String code) throws HttpException {
		return (Provider) Hiber.session().createQuery(
				"from Provider provider where provider.dsoCode.string = :code")
				.setString("code", code).uniqueResult();
	}

	private DsoCode code;

	public Dso(String name, Participant participant, Date validFrom,
			Date validTo, DsoCode code) throws HttpException {
		super(name, participant, MarketRole.DISTRIBUTOR, validFrom, validTo);
		setCode(code);
	}

	public Dso() {
		super();
	}

	void setCode(DsoCode code) {
		this.code = code;
	}

	public DsoCode getCode() {
		return code;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "dso");
		if (code != null) {
			element.setAttribute("code", code.toString());
		}
		return element;
	}
	
	public Llfc getLlfc(LlfcCode llfcCode, Date date) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.code = :code and llfc.validFrom <= :date and (llfc.validTo is null or llfc.validTo >= :date)")
				.setEntity("dso", this).setInteger("code", llfcCode.getInteger())
				.setTimestamp("date", date).uniqueResult();
		if (llfc == null) {
			throw new UserException(
					"There is no line loss factor with the code " + llfcCode
							+ " associated with the DNO '"
							+ getCode().toString() + "' for the date "
							+ date.toString() + ".");
		}
		return llfc;
	}

	public Llfc getLlfc(LlfcCode code) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.code = :code and llfc.validTo is null")
				.setEntity("dso", this).setInteger("code", code.getInteger())
				.uniqueResult();
		if (llfc == null) {
			throw new UserException("There is no ongoing LLFC with the code "
					+ code + " associated with this DNO.");
		}
		return llfc;
	}
	public DsoServices servicesInstance() {
		return new DsoServices(this);
	}
	
	public DsoService insertService(String name, HhEndDate startDate,
			String chargeScript) throws HttpException {
		DsoService service = findDsoService(name);
		if (service == null) {
			service = new DsoService(this, name, startDate, chargeScript);
		} else {
			throw new UserException(
					"There is already a DSO service with this name.");
		}
		Hiber.session().save(service);
		Hiber.flush();
		return service;
	}
	public DsoService findService(String name) throws HttpException {
return (DsoService) Hiber
		.session()
		.createQuery(
				"from DsoService service where service.provider = :provider and service.name = :serviceName")
		.setEntity("provider", this).setString("serviceName", name)
		.uniqueResult();
}

	@Override
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Llfcs.URI_ID.equals(uriId)) {
			return new Llfcs(this);
		} else if (MpanTops.URI_ID.equals(uriId)) {
			return new MpanTops(this);
		} else {
			throw new NotFoundException();
		}
	}

}
