"""
Demo script for the User Onboarding Flow

This demonstrates the onboarding wizard functionality that can be
integrated into the main Streamlit application.
"""

import streamlit as st
import sys
from pathlib import Path

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from ui.streamlit.user_onboarding import create_user_onboarding_flow

def main():
    """Run the onboarding demo"""
    st.set_page_config(
        page_title="Financial Analysis Pro - Onboarding Demo",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.title("🎯 Financial Analysis Pro - Onboarding Demo")

    # Create onboarding flow
    onboarding_flow = create_user_onboarding_flow()

    # Show demo controls
    with st.sidebar:
        st.header("🛠️ Demo Controls")

        if st.button("🔄 Reset Onboarding"):
            for key in list(st.session_state.keys()):
                if 'onboard' in key.lower():
                    del st.session_state[key]
            st.rerun()

        if st.button("⏭️ Force Show Onboarding"):
            st.session_state.show_onboarding = True
            st.session_state.onboarding_step = 0
            st.rerun()

        st.divider()

        st.markdown("**Current State:**")
        st.write(f"Show onboarding: {st.session_state.get('show_onboarding', False)}")
        st.write(f"Step: {st.session_state.get('onboarding_step', 0)}")
        st.write(f"Completed: {st.session_state.get('onboarding_completed', False)}")

    # Main content
    if st.session_state.get('show_onboarding', True) or onboarding_flow.should_show_onboarding():
        if onboarding_flow.render_onboarding_flow():
            st.session_state.show_onboarding = False
            st.session_state.onboarding_completed = True
            st.success("🎉 Onboarding completed!")
            st.balloons()
            if st.button("🔄 Try Again"):
                st.session_state.show_onboarding = True
                st.session_state.onboarding_completed = False
                st.session_state.onboarding_step = 0
                st.rerun()
    else:
        st.success("✅ Onboarding completed!")
        st.markdown("""
        ## 🎯 Welcome to Financial Analysis Pro!

        Your personalized financial analysis environment is ready.

        **What you can do now:**
        - 📊 Run FCF Analysis on your companies
        - 💰 Calculate DCF valuations
        - 🏆 Analyze dividend-paying stocks with DDM
        - 📋 Compare companies with P/B analysis
        - 🎯 Use advanced risk analysis and scenario modeling

        **Your preferences have been saved and will be applied throughout the application.**
        """)

        if st.button("🎯 Restart Onboarding Tour"):
            st.session_state.show_onboarding = True
            st.session_state.onboarding_step = 0
            st.session_state.onboarding_data = {}
            st.rerun()


if __name__ == "__main__":
    main()