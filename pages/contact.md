---
title: Contact
description: Show the capabilities of markdown!
template: page
last_updated: 2025-06-29
show_in_nav: false
nav_order: 2
---


<form id="contact-form" method="POST" action="{{ url_for('contact') }}">
    <div class="form-group">
        <label for="name">Name</label>
        <input type="text" id="name" name="name" required 
               maxlength="100" pattern="[A-Za-z0-9\s\-'.]+" 
               title="Please use only letters, numbers, spaces, and basic punctuation">
    </div>
    
    <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" name="email" required maxlength="254">
    </div>
    
    <div class="form-group">
        <label for="subject">Subject</label>
        <input type="text" id="subject" name="subject" required 
               maxlength="200" pattern="[A-Za-z0-9\s\-'.,!?]+"
               title="Please use only letters, numbers, spaces, and basic punctuation">
    </div>
    
    <div class="form-group">
        <label for="message">Message</label>
        <textarea id="message" name="message" required 
                  maxlength="5000" rows="6"></textarea>
    </div>

    <div class="g-recaptcha" 
         data-sitekey="{{ config['RECAPTCHA_SITE_KEY'] }}"
         data-callback="enableSubmit"></div>
    
    <button type="submit" id="submit-button" disabled>Send Message</button>
</form>
