# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Openfisca Mes aides reform 1"""


from __future__ import division

import copy

from numpy import minimum as min_

from openfisca_core import columns, formulas, reforms
from openfisca_france import entities
from openfisca_france.model.prestations.minima_sociaux import cmu


# Build function

def build_reform(tax_benefit_system):

    Reform = reforms.make_reform(
        name = u'Réforme 1',
        reference = tax_benefit_system,
    )

    @Reform.formula
    class cmu_base_ressources(formulas.SimpleFormulaColumn):
        reference = cmu.cmu_base_ressources

    def function(self, simulation, period):
        self.reference
        period = period.start.offset('first-of', 'month').period('month')
        previous_year = period.start.period('year').offset(-1)
        aspa = simulation.calculate('aspa', period)
        ass = simulation.calculate('ass', period)
        asi = simulation.calculate('asi', period)
        af = simulation.calculate('af', period)
        cf = simulation.calculate_divide('cf', period)
        asf = simulation.calculate_divide('asf', period)
        paje_clca = simulation.calculate_add('paje_clca', previous_year)
        paje_prepare = simulation.calculate_add('paje_prepare', previous_year)
        statut_occupation_holder = simulation.compute('statut_occupation', period)
        aide_logement = simulation.calculate('aide_logement', period)
        cmu_forfait_logement_base = simulation.calculate('cmu_forfait_logement_base', period)
        cmu_forfait_logement_al = simulation.calculate('cmu_forfait_logement_al', period)
        age_holder = simulation.compute('age', period)
        cmu_base_ressources_i_holder = simulation.compute('cmu_base_ressources_i', period)
        P = simulation.legislation_at(period.start).cmu

        statut_occupation = self.cast_from_entity_to_roles(statut_occupation_holder)
        statut_occupation = self.filter_role(statut_occupation, role = CHEF)

        cmu_br_i_par = self.split_by_roles(cmu_base_ressources_i_holder, roles = [CHEF, PART])
        cmu_br_i_pac = self.split_by_roles(cmu_base_ressources_i_holder, roles = ENFS)

        age_pac = self.split_by_roles(age_holder, roles = ENFS)

        forfait_logement = (((statut_occupation == 2) + (statut_occupation == 6)) * cmu_forfait_logement_base +
            (aide_logement > 0) * min_(cmu_forfait_logement_al, aide_logement * 12))

        res = cmu_br_i_par[CHEF] + cmu_br_i_par[PART] + forfait_logement

        # Prestations calculées, donc valeurs mensuelles. On estime l'annuel en multipliant par 12
        res += 12 * (aspa + ass + asi + af + cf + asf)

        res += paje_clca + paje_prepare

        for key, age in age_pac.iteritems():
            res += (0 <= age) * (age <= P.age_limite_pac) * cmu_br_i_pac[key]

        return period, res

    return Reform()
