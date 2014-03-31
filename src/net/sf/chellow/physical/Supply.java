/*******************************************************************************
 * 
 *  Copyright (c) 2005-2013 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/

package net.sf.chellow.physical;

import java.net.URI;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.billing.Contract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.hibernate.Criteria;
import org.hibernate.criterion.Restrictions;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Supply extends PersistentEntity {

	static public Supply getSupply(Long id) throws HttpException {
		Supply supply = (Supply) Hiber.session().get(Supply.class, id);
		if (supply == null) {
			throw new UserException("There is no supply with that id.");
		}
		return supply;
	}

	static public Supply getSupply(String mpanCore) {
		Era era = (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.impMpanCore = :mpanCore or era.expMpanCore = :mpanCore")
				.setString("mpanCore", mpanCore).setMaxResults(1)
				.uniqueResult();
		if (era == null) {
			throw new UserException("There isn't an era with the mpan core "
					+ mpanCore);
		}
		return era.getSupply();
	}

	private String name;

	private Source source;

	private GeneratorType generatorType;

	private Contract dnoContract;

	private GspGroup gspGroup;

	private String note;

	private Set<Era> eras;

	public Supply() {
	}

	Supply(String name, Source source, GeneratorType generatorType,
			Contract dnoContract, GspGroup gspGroup, String note)
			throws HttpException {
		setEras(new HashSet<Era>());
		update(name, source, generatorType, dnoContract, gspGroup);
		setNote(note);
	}

	public void update(String name, Source source, GeneratorType generatorType,
			Contract dnoContract, GspGroup gspGroup) throws HttpException {
		if (name == null) {
			throw new InternalException("The supply name " + "cannot be null.");
		}
		name = name.trim();
		if (name.length() == 0) {
			throw new UserException("The supply name can't be blank.");
		}
		setName(name);
		setSource(source);
		if ((source.getCode().equals(Source.GENERATOR_CODE) || source.getCode()
				.equals(Source.GENERATOR_NETWORK_CODE))
				&& generatorType == null) {
			throw new UserException(
					"If the source is 'gen' or 'gen-net', there must be a generator type.");
		}
		setGeneratorType(generatorType);
		setDnoContract(dnoContract);
		setGspGroup(gspGroup);

		if (getSource().getCode().equals(Source.NETWORK_CODE)
				&& dnoContract.getParty().getDnoCode().equals("99")) {
			throw new UserException("A network supply can't have a 99 DNO.");
		}

	}

	public String getName() {
		return name;
	}

	protected void setName(String name) {
		this.name = name;
	}

	public Source getSource() {
		return source;
	}

	protected void setSource(Source source) {
		this.source = source;
	}

	public GeneratorType getGeneratorType() {
		return generatorType;
	}

	protected void setGeneratorType(GeneratorType generatorType) {
		this.generatorType = generatorType;
	}

	public Contract getDnoContract() {
		return dnoContract;
	}

	public void setDnoContract(Contract contract) {
		this.dnoContract = contract;
	}

	public GspGroup getGspGroup() {
		return gspGroup;
	}

	void setGspGroup(GspGroup gspGroup) {
		this.gspGroup = gspGroup;
	}

	public String getNote() {
		return note;
	}

	public void setNote(String note) {
		this.note = note;
	}

	public Set<Era> getEras() {
		return eras;
	}

	void setEras(Set<Era> eras) {
		this.eras = eras;
	}

	public Eras getErasInstance() {
		return new Eras(this);
	}

	public Era getEraFirst() {
		return (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply order by era.startDate.date")
				.setEntity("supply", this).setMaxResults(1).uniqueResult();
	}

	public Era getEraLast() {
		return (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply.id = :id order by era.finishDate.date desc")
				.setLong("id", getId()).setMaxResults(1).list().get(0);
	}

	public Era getEra(HhStartDate date) {
		if (date == null) {
			return getEraFinishing(null);
		} else {
			return (Era) Hiber
					.session()
					.createQuery(
							"from Era era where era.supply = :supply and era.startDate.date <= :date and (era.finishDate.date >= :date or era.finishDate.date is null)")
					.setEntity("supply", this)
					.setTimestamp("date", date.getDate()).uniqueResult();
		}
	}

	public Era getEraFinishing(HhStartDate finishDate) {
		Criteria criteria = Hiber.session().createCriteria(Era.class);
		if (finishDate == null) {
			criteria.add(Restrictions.isNull("finishDate.date"));
		} else {
			criteria.add(Restrictions.eq("finishDate.date",
					finishDate.getDate()));
		}
		criteria.createCriteria("supply").add(Restrictions.eq("id", getId()));
		return (Era) criteria.uniqueResult();
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "supply");
		element.setAttribute("name", name);
		element.setAttribute("note", note);
		return element;
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.SUPPLIES_INSTANCE.getUrlPath().resolve(getUriId())
				.append("/");
	}

	public Era getEraPrevious(Era era) throws HttpException {
		return (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply and era.finishDate.date = :eraFinishDate")
				.setEntity("supply", this)
				.setTimestamp("eraFinishDate",
						era.getStartDate().getPrevious().getDate())
				.uniqueResult();
	}

	public Era getEraNext(Era era) throws HttpException {
		if (era.getFinishDate() == null) {
			return null;
		}
		return (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply and era.startDate.date = :eraStartDate")
				.setEntity("supply", this)
				.setTimestamp("eraStartDate",
						era.getFinishDate().getNext().getDate()).uniqueResult();
	}

	@SuppressWarnings("unchecked")
	public List<Era> getEras(HhStartDate from, HhStartDate to) {
		List<Era> eras = null;
		if (to == null) {
			eras = (List<Era>) Hiber
					.session()
					.createQuery(
							"from Era era where era.supply = :supply and (era.finishDate.date >= :fromDate or era.finishDate.date is null) order by era.finishDate.date")
					.setEntity("supply", this)
					.setTimestamp("fromDate", from.getDate()).list();
		} else {
			eras = (List<Era>) Hiber
					.session()
					.createQuery(
							"from Era era where era.supply = :supply and era.startDate.date <= :toDate and (era.finishDate.date >= :fromDate or era.finishDate.date is null) order by era.finishDate.date")
					.setEntity("supply", this)
					.setTimestamp("fromDate", from.getDate())
					.setTimestamp("toDate", to.getDate()).list();
		}
		return eras;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element supplyElement = (Element) toXml(
				doc,
				new XmlTree("eras").put("source").put("generatorType")
						.put("gspGroup"));
		source.appendChild(supplyElement);
		for (Source supplySource : (List<Source>) Hiber.session()
				.createQuery("from Source source order by source.code").list()) {
			source.appendChild(supplySource.toXml(doc));
		}
		for (GeneratorType type : (List<GeneratorType>) Hiber.session()
				.createQuery("from GeneratorType type order by type.code")
				.list()) {
			source.appendChild(type.toXml(doc));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		for (GspGroup group : (List<GspGroup>) Hiber.session()
				.createQuery("from GspGroup group order by group.code").list()) {
			source.appendChild(group.toXml(doc));
		}

		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Eras.URI_ID.equals(uriId)) {
			return getErasInstance();
		} else {
			throw new NotFoundException();
		}
	}
}
