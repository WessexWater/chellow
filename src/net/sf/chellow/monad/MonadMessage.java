/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.monad;

import java.util.*;

import net.sf.chellow.monad.types.MonadObject;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MonadMessage extends MonadObject {
	static public final String PARAMETER_REQUIRED = "parameter_required";

	// takes one paramter, 'name', which is the name of the parameter.
	static public final String TOO_MANY_PARAMETER_VALUES = "too_many_parameter_values";

	// takes one paramter, 'name', which is the name of the parameter.
	static public final String STRING_TOO_LONG = "string_too_long";

	// takes one parameter, 'max_length'.
	static public final String STRING_TOO_SHORT = "string_too_short";

	// takes one parameter, 'min_length'.
	static public final String NOT_FOUND = "not_found";

	// takes two parameters, 'type' and 'id'.
	static public final String NOT_RECOGNIZED = "not_recognized";

	// takes a parameter 'recognized_value' for each recognized
	// value
	static public final String CHARACTER_OUTSIDE_BLOCK = "character_outside_block";

	// takes two parameters, 'position' and 'block'

	static public final String NUMBER_TOO_BIG = "number_too_big";

	// takes two parameters, 'number' and 'max'

	static public final String NUMBER_TOO_SMALL = "number_too_small";

	// takes two parameters, 'number' and 'min'

	private String code;

	private String description;

	private List<VFParameter> params;

	public MonadMessage(String description) {
		init(description, null, null);
	}

	public MonadMessage(String description, String code) {
		init(description, code, null);
	}

	public MonadMessage(String description, VFParameter[] params) {
		init(description, null, params);
	}

	public MonadMessage(String description, String code, VFParameter[] params) {
		init(description, code, params);
	}

	private void init(String description, String code, VFParameter[] params) {
		this.code = code;
		if (description == null) {
			throw new IllegalArgumentException(
					"The 'description' parameter must not" + " be null.");
		}
		this.description = description;
		if (params == null) {
			this.params = new ArrayList<VFParameter>();
		} else {
			this.params = Arrays.asList(params);
		}
	}

	public MonadMessage(String description, VFParameter param) {
		init(description, null, null);
		params.add(param);
	}

	public MonadMessage(String description, String code, VFParameter param) {
		init(description, code, null);
		params.add(param);
	}
	
	public MonadMessage(String description, String code, String paramName, String paramValue) {
		init(description, code, null);
		params.add(new VFParameter(paramName, paramValue));
	}


	public String getCode() {
		return code;
	}

	public String getDescription() {
		return description;
	}

	/*
	public Iterator getParameters() {
		return params.iterator();
	}
	*/
	
	public String toString() {
		return getDescription();
	}

	public Element toXml(Document doc) {
		Element elem = doc.createElement("message");

		if (code != null) {
			elem.setAttribute("code", getCode());
		}
		elem.setAttribute("description", getDescription());
		for (VFParameter parameter : params) {
			elem.appendChild(parameter.toXML(doc));
		}
		return elem;
	}
}