package net.sf.chellow.physical;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Channels extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("channels");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private SupplyGeneration generation;

	public Channels(SupplyGeneration generation) {
		this.generation = generation;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return generation.getUri().resolve(getUriId());
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element channelsElement = toXml(doc);
		source.appendChild(channelsElement);
		channelsElement.appendChild(generation.toXml(doc, new XmlTree("supply",
				new XmlTree("organization"))));
		for (Channel channel : generation.getChannels()) {
			channelsElement.appendChild(channel.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		return (Channel) Hiber
				.session()
				.createQuery(
						"from Channel channel where channel.supplyGeneration = :supplyGeneration and channel.id = :channelId")
				.setEntity("supplyGeneration", generation).setLong("channelId",
						Long.parseLong(uriId.getString())).uniqueResult();
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("channels");
	}
}
