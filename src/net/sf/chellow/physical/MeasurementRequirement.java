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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;

public class MeasurementRequirement extends PersistentEntity {
	static public MeasurementRequirement getMeasurementRequirement(Long id)
			throws HttpException {
		MeasurementRequirement requirement = (MeasurementRequirement) Hiber
				.session().get(MeasurementRequirement.class, id);
		if (requirement == null) {
			throw new UserException(
					"There is no measurement requirement with that id.");
		}
		return requirement;
	}


	private Ssc ssc;

	private Tpr tpr;

	public MeasurementRequirement() {
	}

	public MeasurementRequirement(Ssc ssc, Tpr tpr) throws HttpException {
		setSsc(ssc);
		setTpr(tpr);
	}

	void setSsc(Ssc ssc) {
		this.ssc = ssc;
	}

	public Ssc getSsc() {
		return ssc;
	}

	public Tpr getTpr() {
		return tpr;
	}

	void setTpr(Tpr tpr) {
		this.tpr = tpr;
	}
}
