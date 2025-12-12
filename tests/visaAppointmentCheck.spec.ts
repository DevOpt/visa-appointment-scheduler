import { test, expect } from '@playwright/test';
import sgMail from '@sendgrid/mail';

test('Check Appointment Availability', async ({ page }) => {
    // Get environment variables
    const userEmail = process.env.USER_EMAIL;
    const userPassword = process.env.USER_PASSWORD;

    if (!userEmail || !userPassword) {
        throw new Error('USER_EMAIL or USER_PASSWORD environment variable is not set');
    }

    // Sign in to the visa appointment website  
    await page.goto('https://ais.usvisa-info.com/en-ca/iv/users/sign_in');
    await page.fill('input[name="user[email]"]', userEmail);
    await page.fill('input[name="user[password]"]', userPassword);
    await page.click('label[for="policy_confirmed"]');
    await page.click('input[name="commit"][value="Sign In"]');
    await page.waitForTimeout(3000);
    
    // Navigate to the appointment scheduling page
    const continueLink = page.locator('a:has-text("Continue")');
    await continueLink.click();
    await page.waitForTimeout(3000);
    const accordionTitle = page.locator('a.accordion-title:has(h5:text-matches(".*Pay Visa Fee.*"))');
    await accordionTitle.waitFor({ state: 'visible' });
    const accordionItem = accordionTitle.locator('xpath=./ancestor::li[contains(@class, "accordion-item")]');
    const classAttr = await accordionItem.getAttribute('class');
    if (!classAttr?.includes('is-active')) {
        await accordionTitle.click();
        await page.waitForTimeout(1000);
        console.log("Expanded Pay Visa Fee accordion");
    }
    const payFeeButton = page.locator('a.button:has-text("Pay Visa Fee")');
    await payFeeButton.waitFor({ state: 'visible' });
    await payFeeButton.click();

    // Check for appointment availability
    await page.waitForTimeout(2000);
    const noAppointmentsMsg = page.locator("div.noPaymentAcceptedMessage h3:has-text('There are no available appointments at this time')");
    const montrealNoAppointments = page.locator("tr:has(td:text('Montreal')):has(td:text-matches('.*No Appointments Available.*'))");
    const generalMessageVisible = await noAppointmentsMsg.isVisible();
    const montrealMessageVisible = await montrealNoAppointments.isVisible();
    if (generalMessageVisible || montrealMessageVisible) {
        console.log('No appointment slots are available.');
    } else {
        console.log('Appointment slots are available!');
        await sendEmailNotification();
    }
});

// Helper function to send email notifications
async function sendEmailNotification() {
    const apiKey = process.env.SENDGRID_API_KEY;
    if (!apiKey) {
        throw new Error('SENDGRID_API_KEY environment variable is not set');
    }
    sgMail.setApiKey(apiKey);

    const msg = {
    to: 'wefa.sherif@gmail.com', 
    from: 'auth@asherif.dev',
    subject: 'U.S Visa Appointment Has Opened!',
    html: '<p>We have checked the visa appointment availability and found a slot. Go to <a href="https://ais.usvisa-info.com/en-ca/iv/users/sign_in">U.S Visa Appointment Service</a> to schedule your appointment.</p>',
    }

    sgMail
    .send(msg)
    .then((response) => {
        console.log(response[0].statusCode)
        console.log(response[0].headers)
    })
    .catch((error) => {
        console.error(error)
    })
}