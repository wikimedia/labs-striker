# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Wikimedia Foundation and contributors.
# All Rights Reserved.
#
# This file is part of Striker.
#
# Striker is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Striker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Striker.  If not, see <http://www.gnu.org/licenses/>.

from operator import attrgetter
import logging

from django.conf import settings
from django.db import IntegrityError
from django.db import models
from django.db import transaction
from django.utils import timezone

from striker.goals import GOALS
from striker.goals import GOALS_BY_ID


logger = logging.getLogger(__name__)


class MilestoneManager(models.Manager):
    use_for_related_fields = True

    def recordMilestone(self, goal, user=None):
        if user is None:
            if hasattr(self, 'core_filters') and 'user' in self.core_filters:
                user = self.core_filters['user']
            else:
                raise TypeError(
                    'user required unless called from RelatedManager')
        try:
            # Wrap in transaction.atomic() to avoid breaking outer
            # transactions that may be running when this is called via
            # a post_save hook
            # http://stackoverflow.com/a/23326971/8171
            with transaction.atomic():
                self.model(goal=goal, user=user).save(force_insert=True)
        except IntegrityError:
            # this just means that the user already reached this milestone
            pass

    def nextGoal(self, user=None):
        if user is not None:
            achieved = self.filter(user=user)
        elif hasattr(self, 'core_filters') and 'user' in self.core_filters:
            achieved = self.all()
        else:
            raise TypeError('user required unless called from RelatedManager')

        achieved = achieved.values_list('goal', flat=True).order_by('goal')
        percent = (len(achieved) / len(GOALS)) * 100
        if percent < 100:
            val = sorted(g for g in GOALS.values() if g not in achieved)[0]
            ret = {
                'id': val,
                'name': GOALS_BY_ID[val],
                'percentage': percent,
            }
        else:
            ret = {'percentage': percent}
        return ret

    def allGoals(self, user=None):
        if user is not None:
            achieved = self.filter(user=user)
        elif hasattr(self, 'core_filters') and 'user' in self.core_filters:
            achieved = self.all()
        else:
            raise TypeError('user required unless called from RelatedManager')

        achieved = list(
            achieved.values_list('goal', flat=True).order_by('goal'))
        percent = (len(achieved) / len(GOALS)) * 100

        goals = []
        for name, val in goals.iteritems():
            goals.append({
                'id': val,
                'name': name,
                'percentage': percent,
                'completed': val in achieved,
            })
        return sorted(goals, key=attrgetter('id'))


class Milestone(models.Model):
    goal = models.SmallIntegerField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_index=True, related_name='milestones', on_delete=models.CASCADE)
    completed_date = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)

    objects = MilestoneManager()

    class Meta:
        unique_together = ('user', 'goal')

    @property
    def name(self):
        return GOALS_BY_ID[self.goal]

    def __str__(self):
        return '{0}: {1}'.format(self.user, self.name)
