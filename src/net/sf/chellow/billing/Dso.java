package net.sf.chellow.billing;

import java.util.Date;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.DsoCode;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Llfc;
import net.sf.chellow.physical.Llfcs;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.MpanTops;
import net.sf.chellow.physical.Participant;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Dso extends Party {
	static public Dso getDso(Long id) throws HttpException {
		Dso dso = (Dso) Hiber.session().get(Dso.class, id);
		if (dso == null) {
			throw new UserException("There is no DSO with the id '" + id + "'.");
		}
		return dso;
	}

	static public Dso getDso(Participant participant) throws HttpException {
		Dso dso = (Dso) Hiber.session().createQuery(
				"from Dso dso where dso.participant = :participant").setEntity(
				"participant", participant).uniqueResult();
		if (dso == null) {
			throw new UserException("There is no DSO with the participant '"
					+ participant.getCode() + "'.");
		}
		return dso;
	}

	static public Dso getDso(DsoCode code) throws HttpException {
		Dso dso = findDso(code.getString());
		if (dso == null) {
			throw new UserException("There is no DSO with the code '" + code
					+ "'.");
		}
		return dso;
	}

	static public Dso findDso(String code) throws HttpException {
		return (Dso) Hiber.session().createQuery(
				"from Dso dso where dso.code.string = :code").setString("code",
				code).uniqueResult();
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
		element.setAttribute("code", code.toString());
		return element;
	}

	public Llfc getLlfc(String code, Date date) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.code = :code and llfc.validFrom <= :date and (llfc.validTo is null or llfc.validTo >= :date)")
				.setEntity("dso", this).setInteger("code",
						Integer.parseInt(code)).setTimestamp("date", date)
				.uniqueResult();
		if (llfc == null) {
			throw new UserException(
					"There is no line loss factor with the code " + code
							+ " associated with the DNO '"
							+ getCode().toString() + "' for the date "
							+ date.toString() + ".");
		}
		return llfc;
	}

	public Llfc getLlfc(String code) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.code = :code and llfc.validTo is null")
				.setEntity("dso", this).setInteger("code", Integer.parseInt(code))
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
		DsoService service = findService(name);
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
						"from DsoService service where service.dso = :dso and service.name = :serviceName")
				.setEntity("dso", this).setString("serviceName", name)
				.uniqueResult();
	}

	@Override
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Llfcs.URI_ID.equals(uriId)) {
			return new Llfcs(this);
		} else if (MpanTops.URI_ID.equals(uriId)) {
			return new MpanTops(this);
		} else if (DsoServices.URI_ID.equals(uriId)) {
			return new DsoServices(this);
		} else {
			throw new NotFoundException();
		}
	}

}
