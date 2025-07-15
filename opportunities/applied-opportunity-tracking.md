# Applied Opportunity Tracking Feature

This document explains the new functionality added to track when a user has **applied** to an opportunity simply by viewing its detail page. It also shows how the frontend can determine which opportunities the user has already applied to when listing them.


## Feature Overview
- **Automatic Application Tracking**:  
  When an authenticated user visits the detail page of an opportunity, the system will **automatically mark it as applied**.

- **Frontend Visibility**:  
  The list of opportunities returned from the API will now include an additional boolean field:  
  ```json
  "is_applied": true | false
