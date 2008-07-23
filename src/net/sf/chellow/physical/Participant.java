package net.sf.chellow.physical;

import javax.servlet.ServletContext;

import net.sf.chellow.billing.Provider;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Participant extends PersistentEntity {
	static public Participant getParticipant(Long id) throws HttpException {
		Participant participant = (Participant) Hiber.session().get(
				Participant.class, id);
		if (participant == null) {
			throw new NotFoundException();
		}
		return participant;
	}

	static public Participant getParticipant(String code) throws HttpException {
		Participant participant = (Participant) Hiber.session().createQuery(
				"from Participant participant where participant.code = :code")
				.setString("code", code).uniqueResult();
		if (participant == null) {
			throw new NotFoundException();
		}
		return participant;
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add Participants.");
		Mdd mdd = new Mdd(sc, "MarketParticipant", new String[] {
				"Market Participant Id", "Market Participant Name",
				"Pool Member Id" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			Participant participant = new Participant(values[0], values[1]);
			Hiber.session().save(participant);
			Hiber.close();
		}
		Debug.print("Finished adding Participants.");
	}

	private String code;
	private String name;

	public Participant() {

	}

	public Participant(String code, String name) {
		this.code = code;
		this.name = name;
	}

	public String getCode() {
		return code;
	}

	public void setCode(String code) {
		this.code = code;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	@Override
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public MonadUri getUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	@Override
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = (Element) doc.getFirstChild();

		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws HttpException {
		setTypeName("participant");
		Element element = (Element) super.toXml(doc);

		element.setAttribute("code", code);
		element.setAttribute("name", name);
		return element;
	}

	public Provider getProvider(char roleCode) {
		return (Provider) Hiber
				.session()
				.createQuery(
						"from Provider provider where provider.participant = :participant and provider.role.code = :roleCode")
				.setEntity("participant", this).setCharacter("roleCode",
						roleCode).uniqueResult();
	}
}
