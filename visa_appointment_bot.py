import os
import platform
import sendgrid
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from sendgrid.helpers.mail import Mail, Email, To, Content
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time


class VisaAppointmentBot:
    def __init__(self):
        # Configure Chrome options
        chrome_options = Options()
        
        # Add headless mode for non-MacBook environments
        if platform.system() != "Darwin":  # Darwin is macOS
            chrome_options.add_argument("--headless")
            print("Running in headless mode (non-macOS system)")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Get credentials securely
        self.username = os.getenv("VISA_USER_USERNAME")
        self.password = os.getenv("VISA_USER_PASSWORD")
        
        # Use ChromeDriverManager for automatic driver management
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def login(self, username, password):
        """Login to the visa application portal"""
        try:
            # Navigate to the login page
            self.driver.get("https://ais.usvisa-info.com/en-ca/iv/")

            # Click on the Sign In link
            sign_in_link = self.wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))
            )
            sign_in_link.click()
            time.sleep(2)
            
            # Wait for and fill username field
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "user[email]"))  # Adjust selector as needed
            )
            username_field.send_keys(username)
            
            # Wait for and fill password field
            password_field = self.driver.find_element(By.NAME, "user[password]")  # Adjust selector as needed
            password_field.send_keys(password)
            
            # Click on the checkbox to accept terms if present 
            try:
                # Try clicking the label first (most reliable for custom checkboxes)
                checkbox_label = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//label[@for='policy_confirmed']"))
                )
                checkbox_label.click()
                print("Policy checkbox checked via label")
            except Exception as e:
                try:
                    # Fallback: try clicking the div wrapper
                    checkbox_div = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'icheckbox')]"))
                    )
                    checkbox_div.click()
                    print("Policy checkbox checked via div wrapper")
                except Exception as e2:
                    try:
                        # Last resort: try the checkbox itself with JavaScript
                        checkbox = self.driver.find_element(By.ID, "policy_confirmed")
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        print("Policy checkbox checked via JavaScript")
                    except Exception as e3:
                        print(f"All checkbox click methods failed: {e}, {e2}, {e3}")
            
            # Find and click login button
            login_button = self.driver.find_element(By.XPATH, "//input[@name='commit' and @value='Sign In']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(3)
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
            
        return True
    
    def send_notification(self):
        sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        from_email = Email("adume.co@gmail.com")
        to_email = To("abdurahman.sherif@gmail.com")
        subject = "K1 Visa Appointment Notification"
        content = Content("text/plain", "You may have a new K1 visa appointment openings. Please check the portal for details.")
        mail = Mail(from_email, to_email, subject, content)

        # Get a JSON-ready representation of the Mail object
        mail_json = mail.get()

        # Send an HTTP POST request to /mail/send
        response = sg.client.mail.send.post(request_body=mail_json)
        print(response.status_code)
    
    def navigate_to_appointment_section(self):
        """Navigate to the appointment booking section"""
        try:
            # Example: Click on "Continue" or "Schedule Appointment" button
            continue_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Continue')]"))
            )
            continue_button.click()
            time.sleep(2)
            # Expand the "Pay Visa Fee" dropdown and click the button
            try:
                # Check if accordion is already expanded, if not click to expand
                accordion_title = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'accordion-title') and .//h5[contains(., 'Pay Visa Fee')]]"))
                )
                
                # Check if accordion is already expanded
                accordion_item = accordion_title.find_element(By.XPATH, "./ancestor::li[@class='accordion-item' or contains(@class, 'accordion-item')]")
                
                if 'is-active' not in accordion_item.get_attribute('class'):
                    accordion_title.click()
                    time.sleep(1)
                    print("Expanded Pay Visa Fee accordion")
                
                # Click the "Pay Visa Fee" button
                pay_fee_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'button') and contains(text(), 'Pay Visa Fee')]"))
                )
                pay_fee_button.click()
                print("Clicked Pay Visa Fee button")
                time.sleep(2)
                
            except Exception as e:
                print(f"Failed to handle Pay Visa Fee section: {e}")
                return False
            
        except Exception as e:
            print(f"Navigation failed: {e}")
            return False
            
        return True
    
    def check_appointment_availablity(self):
        """Check for available appointment dates"""
        # check if this element exists with the text
        try:
            no_appointments_msg = self.driver.find_element(
                By.XPATH, 
                "//div[@class='noPaymentAcceptedMessage']//h3[contains(text(), 'There are no available appointments at this time')]"
            )

            montreal_no_appointments = self.driver.find_element(
                By.XPATH,
                "//tr[td[text()='Montreal'] and td[contains(text(), 'No Appointments Available')]]"
            )
            
            if no_appointments_msg or montreal_no_appointments:
                return False   
                       
        except Exception as e:
            print("Appointments may be available - message not found")

        return True
    
    def select_appointment_slot(self):
        """Select an available appointment slot"""
        try:
            # Example: Click on first available date
            first_available = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "available-date"))
            )
            first_available.click()
            time.sleep(2)
            
            # Confirm selection
            confirm_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
            confirm_button.click()
            time.sleep(2)
            
        except Exception as e:
            print(f"Appointment selection failed: {e}")
            return False
            
        return True
    
    def run(self):
        """Main execution function"""
        
        try:
            # Perform login
            if self.login(self.username, self.password):
                print("Login successful!")
                
                # Navigate to appointment section
                if self.navigate_to_appointment_section():
                    print("Navigated to appointment section")
                    
                    # Check for available dates
                    if self.check_appointment_availablity():
                        print("Available dates found!")
                        self.send_notification()
                    else:
                        print("No available dates")
                else:
                    print("Failed to navigate to appointment section")
            else:
                print("Login failed")
                
        except Exception as e:
            print(f"An error occurred: {e}")
            
        finally:
            # Keep browser open for a while to see results
            if platform.system() == "Darwin":  # Only for macOS
                input("Press Enter to close the browser...")
                self.driver.quit()
            else:
                self.driver.quit()

if __name__ == "__main__":
    bot = VisaAppointmentBot()
    bot.run()