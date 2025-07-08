import math
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache 
from opportunities.models import Opportunity  

class OpportunityMatcher:
    """
    Core matching algorithm that matches users to opportunities based on
    their profile data, preferences, and the opportunity requirements.
    """

    def __init__(self, user_profile):
        self.user_profile = user_profile
        self.weights = {
            'skills_match': 0.4,
            'location_match': 0.2,
            'education_match': 0.25,
            'preferences_match': 0.15,
        }

    def get_recommended_opportunities(self, limit=20, offset=0, filters=None):
        """
        Returns personalized opportunity recommendations for the user.
        """
        cache_key = f'user_recommendations_{self.user_profile.user.id}'
        cached_result = cache.get(cache_key)

        if cached_result and not filters:
            return cached_result[offset:offset + limit]

        queryset = Opportunity.objects.filter(
            deadline__gte=timezone.now().date()
        )

        if filters:
            queryset = self._apply_filters(queryset, filters)

        scored_opportunities = self._score_opportunities(queryset)

        sorted_results = sorted(
            scored_opportunities,
            key=lambda x: x['score'],
            reverse=True
        )

        if not filters:
            cache.set(cache_key, sorted_results, 60 * 30)  

        return sorted_results[offset:offset + limit]
    
def _apply_filters(self, queryset, filters):
    """
    Apply user-specified filters to the queryset.
    """
    if 'type' in filters:
        queryset = queryset.filter(type=filters['type'])

    if 'location' in filters:
        queryset = queryset.filter(
            Q(location__icontains=filters['location']) |
            Q(is_remote=True)
        )

    if 'category' in filters:
        queryset = queryset.filter(category__slug=filters['category'])

    if 'tags' in filters:
        for tag in filters['tags']:
            queryset = queryset.filter(tags__slug=tag)

    if 'skills' in filters:
        for skill in filters['skills']:
            queryset = queryset.filter(skills_required__contains=[skill])

    if 'deadline_after' in filters:
        queryset = queryset.filter(deadline__gte=filters['deadline_after'])

    if 'deadline_before' in filters:
        queryset = queryset.filter(deadline__lte=filters['deadline_before'])

    if 'education_level' in filters:
        queryset = queryset.filter(eligibility_criteria__education_level=filters['education_level'])

    if 'posted_within' in filters:
        now = timezone.now()
        posted_within = filters['posted_within']
        if posted_within == 'today':
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)
            queryset = queryset.filter(created_at__gte=since)
        elif posted_within == 'this_week':
            start_of_week = now - timezone.timedelta(days=now.weekday())
            queryset = queryset.filter(created_at__gte=start_of_week)
        elif posted_within == 'this_month':
            since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            queryset = queryset.filter(created_at__gte=since)
        elif posted_within.endswith('h'):
            try:
                hours = int(posted_within.replace('h', ''))
                since = now - timezone.timedelta(hours=hours)
                queryset = queryset.filter(created_at__gte=since)
            except ValueError:
                pass

    return queryset


    def _score_opportunities(self, queryset):
        """
        Score each opportunity based on profile and preferences.
        """
        results = []
        user_skills = set(self.user_profile.skills)
        user_education = self.user_profile.education
        user_preferences = self.user_profile.preferences
        user_location = self.user_profile.location.lower()

        for opportunity in queryset:
            skills_score = self._calculate_skills_score(user_skills, opportunity.skills_required)
            location_score = self._calculate_location_score(opportunity, user_location)
            education_score = 1 if self._check_eligibility(opportunity.eligibility_criteria, user_education) else 0
            preferences_score = self._calculate_preference_score(user_preferences, opportunity)

            total_score = (
                self.weights['skills_match'] * skills_score +
                self.weights['location_match'] * location_score +
                self.weights['education_match'] * education_score +
                self.weights['preferences_match'] * preferences_score
            )

            # Apply boosts
            if opportunity.is_featured:
                total_score *= 1.1

            days_old = (timezone.now().date() - opportunity.created_at.date()).days
            recency_boost = max(0, 1 - (days_old / 30))
            total_score *= (1 + recency_boost * 0.1)

            final_score = min(100, math.floor(total_score * 100))

            results.append({
                'opportunity': opportunity,
                'score': final_score,
                'reasons': {
                    'skills_match': round(skills_score * 100),
                    'location_match': round(location_score * 100),
                    'eligibility': "Eligible" if education_score else "Not eligible",
                    'preference_match': round(preferences_score * 100),
                }
            })

        return results

    def _calculate_skills_score(self, user_skills, opp_skills_list):
        opp_skills = set(opp_skills_list)
        if not opp_skills:
            return 1.0
        return len(user_skills & opp_skills) / len(opp_skills)

    def _calculate_location_score(self, opportunity, user_location):
        if opportunity.is_remote:
            return 1.0
        if opportunity.location and opportunity.location.lower() in user_location:
            return 1.0
        return 0.2

    def _calculate_preference_score(self, preferences, opportunity):
        score = 0
        if preferences.get('preferred_type') == opportunity.type:
            score += 0.5
        if preferences.get('preferred_category') == opportunity.category.slug:
            score += 0.5
        return score

    def _check_eligibility(self, criteria, user_education):
        if not criteria:
            return True

        education_levels = ['high_school', 'bachelors', 'masters', 'phd']
        user_level = user_education.get('highest_level')
        required_level = criteria.get('education_level')

        if required_level and user_level:
            try:
                if education_levels.index(user_level) < education_levels.index(required_level):
                    return False
            except ValueError:
                return False

        user_age = user_education.get('age')
        if user_age is not None:
            min_age = criteria.get('min_age')
            max_age = criteria.get('max_age')
            if min_age is not None and user_age < min_age:
                return False
            if max_age is not None and user_age > max_age:
                return False

        required_nationalities = criteria.get('nationalities')
        user_nationality = user_education.get('nationality')
        if required_nationalities and user_nationality not in required_nationalities:
            return False

        return True
